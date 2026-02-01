from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from store.api.serializers import PurchaseRequestSerializer, ProductRegisterSerializer
from store.services.purchase import purchase_one,PurchaseError
from store.services.register.product import register_product

class PurchaseView(APIView):
    """
    商品購入API
    student_id,jan_code
    """
    def post(self, request):
        serializer = PurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = purchase_one(
                student_id=serializer.validated_data["student_id"],
                jan_code=serializer.validated_data["jan_code"],
            )
        except PurchaseError as e:
            if e.code in ("user_not_found", "product_not_found"):
                return Response({"error": e.code}, status=status.HTTP_404_NOT_FOUND)
            if e.code == "out_of_stock":
                return Response({"error": e.code}, status=status.HTTP_409_CONFLICT)
            return Response({"error": "unknown"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {'ok'},
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