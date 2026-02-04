from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0003_stocktransaction_amended_of"),
    ]

    operations = [
        migrations.AddField(
            model_name="stocktransaction",
            name="unit_cost",
            field=models.IntegerField(blank=True, null=True, verbose_name="仕入単価"),
        ),
    ]
