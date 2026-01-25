from rest_framework import serializers

class PurchaseRequestSerializer(serializers.Serializer):
    student_id_code = serializers.CharField()
    jan_code = serializers.CharField()