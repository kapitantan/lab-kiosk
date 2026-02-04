import csv
import io

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from store.api.serializers import (
    ProductRegisterSerializer,
    PurchaseRequestSerializer,
    StockTransactionSerializer,
)
from store.models import Product, StockTransaction
from store.services.purchase import purchase_one,PurchaseError
from store.services.register.product import register_product

class StockTransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        StockTransaction.objects
        .select_related("product", "user", "amended_of")
        .order_by("-created_at")
    )
    serializer_class = StockTransactionSerializer

    @action(detail=True, methods=["post"], url_path="amend")
    def amend(self, request, pk=None):
        with transaction.atomic():
            tx = get_object_or_404(
                StockTransaction.objects.select_for_update(),
                pk=pk,
            )

            if tx.transaction_type == "CORRECTION":
                return Response(
                    {"error": "cannot_amend_correction"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if tx.amendments.exists():
                return Response(
                    {"error": "already_amended"},
                    status=status.HTTP_409_CONFLICT,
                )

            amend = StockTransaction.objects.create(
                product=tx.product,
                user=tx.user,
                transaction_type="CORRECTION",
                delta=-tx.delta,
                description=f"amend of {tx.id}",
                amended_of=tx,
            )

        serializer = self.get_serializer(amend)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PurchaseView(APIView):
    """
    商品購入API
    {
    "student_id":,
    "jan_code":
    }
    """
    def post(self, request):
        serializer = PurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = purchase_one(
                student_id=serializer.validated_data["student_id"],
                jan_code=serializer.validated_data["jan_code"],
            )
            print({'product':result.product.name,'remaining':result.remaining},flush=True)
        except PurchaseError as e:
            if e.code in ("user_not_found", "product_not_found"):
                return Response({"error": e.code}, status=status.HTTP_404_NOT_FOUND)
            if e.code == "out_of_stock":
                return Response({"error": e.code}, status=status.HTTP_409_CONFLICT)
            return Response({"error": "unknown"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {'product':result.product.name,'remaining':result.remaining},
            # {'ok'},
            status=status.HTTP_200_OK,
        )   


class ProductRegisterView(APIView):
    """
    商品登録API
    must_property
    {
    "jan_code":,
    "name":,
    "price":
}
    """

    # 必要なら認証・権限をここに設定
    # authentication_classes = [...]
    # permission_classes = [...]

    def post(self, request, *args, **kwargs):
        serializer = ProductRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = register_product(validated_data=serializer.validated_data)

        # 返却は「登録結果」を返すのが親切
        # （最低限 jan_code だけ返すでもOK）
        response_serializer = ProductRegisterSerializer(product)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RestockImportView(APIView):
    """
    CSV一括入荷API
    multipart/form-data で file フィールドに CSV を送る
    """
    parser_classes = (MultiPartParser, FormParser)

    ALLOWED_CONTENT_TYPES = {
        "text/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    }

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"status": "error", "message": "file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            upload.content_type
            and upload.content_type not in self.ALLOWED_CONTENT_TYPES
            and not upload.name.lower().endswith(".csv")
        ):
            return Response(
                {"status": "error", "message": "unsupported media type"},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        try:
            text = io.TextIOWrapper(upload.file, encoding="utf-8-sig")
            reader = csv.DictReader(text)
        except Exception:
            return Response(
                {"status": "error", "message": "invalid csv"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_columns = {"jan_code", "quantity"}
        if reader.fieldnames is None:
            return Response(
                {"status": "error", "message": "csv has no header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        missing = required_columns - set(reader.fieldnames)
        if missing:
            return Response(
                {"status": "error", "message": f"missing columns: {', '.join(sorted(missing))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = []
        errors_400 = []
        errors_422 = []
        warnings = []
        total_rows = 0

        for row_index, row in enumerate(reader, start=2):
            total_rows += 1
            jan_code = (row.get("jan_code") or "").strip()
            quantity_raw = (row.get("quantity") or "").strip()
            unit_cost_raw = (row.get("unit_cost") or "").strip()
            name = (row.get("name") or "").strip()

            if not jan_code:
                errors_400.append(
                    {
                        "row": row_index,
                        "code": "MISSING_JAN",
                        "jan_code": "",
                        "field": "jan_code",
                        "message": "jan_codeは必須です",
                    }
                )
                continue

            try:
                quantity = int(quantity_raw)
            except ValueError:
                errors_400.append(
                    {
                        "row": row_index,
                        "code": "INVALID_QUANTITY_TYPE",
                        "jan_code": jan_code,
                        "field": "quantity",
                        "message": "quantityは整数で指定してください",
                    }
                )
                continue

            if quantity < 0:
                errors_422.append(
                    {
                        "row": row_index,
                        "code": "INVALID_QUANTITY",
                        "jan_code": jan_code,
                        "field": "quantity",
                        "message": "quantityは0以上の整数で指定してください",
                    }
                )
                continue

            unit_cost = None
            if unit_cost_raw != "":
                try:
                    unit_cost = int(unit_cost_raw)
                except ValueError:
                    errors_400.append(
                        {
                            "row": row_index,
                            "code": "INVALID_UNIT_COST_TYPE",
                            "jan_code": jan_code,
                            "field": "unit_cost",
                            "message": "unit_costは整数で指定してください",
                        }
                    )
                    continue

            rows.append(
                {
                    "row": row_index,
                    "jan_code": jan_code,
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "name": name,
                }
            )

        if errors_400:
            return Response(
                {
                    "status": "error",
                    "import": {
                        "created_count": 0,
                        "skipped_count": total_rows,
                    },
                    "errors": errors_400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        jan_codes = {row["jan_code"] for row in rows}
        products = Product.objects.filter(jan_code__in=jan_codes)
        product_map = {product.jan_code: product for product in products}

        unknown_errors = []
        for row in rows:
            if row["jan_code"] not in product_map:
                unknown_errors.append(
                    {
                        "row": row["row"],
                        "code": "UNKNOWN_JAN",
                        "jan_code": row["jan_code"],
                        "field": "jan_code",
                        "message": "未登録の商品です。先に商品登録してください",
                    }
                )

        errors_422.extend(unknown_errors)

        if errors_422:
            return Response(
                {
                    "status": "error",
                    "import": {
                        "created_count": 0,
                        "skipped_count": total_rows,
                    },
                    "errors": errors_422,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        for row in rows:
            if row["name"]:
                product = product_map[row["jan_code"]]
                if row["name"] != product.name:
                    warnings.append(
                        {
                            "row": row["row"],
                            "code": "NAME_MISMATCH",
                            "jan_code": row["jan_code"],
                            "field": "name",
                            "message": (
                                f"CSVの商品名とDBの商品名が一致しません（CSV:{row['name']} / DB:{product.name}）"
                            ),
                        }
                    )

        with transaction.atomic():
            transactions = [
                StockTransaction(
                    product=product_map[row["jan_code"]],
                    transaction_type="RESTOCK",
                    delta=row["quantity"],
                    unit_cost=row["unit_cost"],
                )
                for row in rows
            ]
            StockTransaction.objects.bulk_create(transactions)

        return Response(
            {
                "status": "ok",
                "import": {
                    "created_count": len(rows),
                    "skipped_count": 0,
                },
                "warnings": warnings,
            },
            status=status.HTTP_200_OK,
        )
