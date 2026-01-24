from django.db import models
from django.db.models import Sum

class User(models.Model):
    """
    利用者（学生・教職員）モデル
    """
    student_id = models.CharField("学生証番号(バーコード)", max_length=50, unique=True, db_index=True)
    name = models.CharField("氏名", max_length=100)
    # slack_user_id = models.CharField("Slack Member ID", max_length=50, blank=True, null=True, help_text="通知用。Uから始まるID")
    created_at = models.DateTimeField("登録日", auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class Product(models.Model):
    """
    商品モデル
    """
    jan_code = models.CharField("JANコード", max_length=20, unique=True, db_index=True)
    name = models.CharField("商品名", max_length=200)
    price = models.IntegerField("単価")
    image_url = models.URLField("商品画像URL", blank=True, null=True)
    alert_threshold = models.IntegerField("通知閾値", default=3, help_text="在庫がこの数を下回ったら通知")
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        """
        現在の在庫数を計算して返すプロパティ
        すべてのトランザクションの delta を合計する
        """
        # aggregateは {'delta__sum': 10} のような辞書を返す
        result = self.transactions.aggregate(Sum('delta'))
        return result['delta__sum'] or 0


class StockTransaction(models.Model):
    """
    入出庫・購入履歴モデル
    すべての在庫変動はここに記録される
    """
    TYPE_CHOICES = (
        ('PURCHASE', '購入'),   # 在庫減
        ('RESTOCK', '入荷'),    # 在庫増
        ('CORRECTION', '修正'), # 棚卸し調整等
    )

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transactions', verbose_name="商品")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="利用者")
    
    transaction_type = models.CharField("変動タイプ", max_length=20, choices=TYPE_CHOICES)
    delta = models.IntegerField("変動数", help_text="購入ならマイナス、入荷ならプラスの値")
    
    description = models.CharField("備考", max_length=200, blank=True)
    created_at = models.DateTimeField("日時", auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.product.name}: {self.delta} ({self.get_transaction_type_display()})"