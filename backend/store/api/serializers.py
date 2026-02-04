from rest_framework import serializers
from store.models import Product, StockTransaction

class PurchaseRequestSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    jan_code = serializers.CharField()

class ProductRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "jan_code",
            "name",
            "price",
            "image_url",
            "alert_threshold",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def validate_jan_code(self, value: str) -> str:
        """
        JANコードのバリデーション
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError("JANコードは必須です。")

        # 登録API用：既存JANがあれば弾く
        if Product.objects.filter(jan_code=value).exists():
            raise serializers.ValidationError("このJANコードの商品は既に登録されています。")

        return value

    def validate_price(self, value: int) -> int:
        """
        単価のバリデーション
        """
        if value < 0:
            raise serializers.ValidationError("単価は0以上で指定してください。")
        return value

    def validate_alert_threshold(self, value: int) -> int:
        """
        通知閾値のバリデーション
        """
        if value < 0:
            raise serializers.ValidationError("通知閾値は0以上で指定してください。")
        return value

    def validate(self, attrs):
        """
        複数フィールドにまたがるバリデーション（必要なら）
        """
        # 例：高額商品で alert_threshold が 0 は変じゃない？など
        # 今回は特に制約なし
        return attrs


class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "product",
            "user",
            "transaction_type",
            "delta",
            "unit_cost",
            "description",
            "amended_of",
            "created_at",
        ]
        read_only_fields = fields


class RestockImportRequestSerializer(serializers.Serializer):
    file = serializers.FileField()


class RestockRequestSerializer(serializers.Serializer):
    jan_code = serializers.CharField()
    quantity = serializers.IntegerField(min_value=0)
    unit_cost = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
