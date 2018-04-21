# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_testmodel_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='testmodel',
            options={'verbose_name_plural': '测试'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name_plural': '用户'},
        ),
        migrations.AddField(
            model_name='testmodel',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评论'), (5, '已完成')], verbose_name='订单详情'),
        ),
    ]
