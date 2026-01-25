from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from store.api.serializers import PurchaseRequestSerializer
from store.services.purchase import purchase_one,PurchaseError


class PurchaseView(APIView):
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