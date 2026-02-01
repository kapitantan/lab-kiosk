from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from store.api.serializers import (
    ProductRegisterSerializer,
    PurchaseRequestSerializer,
    StockTransactionSerializer,
)
from store.models import StockTransaction
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