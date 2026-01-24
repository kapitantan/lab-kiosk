from django.contrib import admin
from .models import Product, User, StockTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 一覧画面に表示する項目（現在の在庫数も表示！）
    list_display = ('id', 'name', 'price', 'current_stock_display', 'alert_threshold', 'jan_code')
    search_fields = ('name', 'jan_code')
    list_editable = ('price', 'alert_threshold') # 一覧画面で直接価格編集できるようにする

    # @propertyをAdminで表示するための設定
    def current_stock_display(self, obj):
        return obj.current_stock
    current_stock_display.short_description = "現在在庫"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'created_at')
    search_fields = ('name', 'student_id')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'product', 'transaction_type', 'delta', 'user')
    list_filter = ('transaction_type', 'created_at') # 右側にフィルタメニューが出る
    autocomplete_fields = ['product', 'user'] # 商品数が多くなっても検索窓で選べる