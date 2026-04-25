from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0008_order_bonus_points_earned_order_bonus_points_used_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='product',
            name='preorder_delivery_days',
            field=models.PositiveIntegerField(default=7, help_text='Сколько дней нужно на выполнение предзаказа по этому товару', verbose_name='Срок доставки предзаказа (дней)'),
        ),
    ]
