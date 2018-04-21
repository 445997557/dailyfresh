from django.contrib.auth.models import AbstractUser
from django.db import models
from tinymce.models import HTMLField

from utils.models import BaseModel


class User(BaseModel, AbstractUser):

    class Meta:
        db_table = 'df_user'
        verbose_name_plural = '用户'


class Address(BaseModel):
    """地址"""

    receiver_name = models.CharField(max_length=20, verbose_name="收件人")
    receiver_mobile = models.CharField(max_length=11, verbose_name="联系电话")
    detail_addr = models.CharField(max_length=256, verbose_name="详细地址")
    zip_code = models.CharField(max_length=6, null=True, verbose_name="邮政编码")
    is_default = models.BooleanField(default=False, verbose_name='默认地址')

    user = models.ForeignKey(User, verbose_name="所属用户")

    class Meta:
        db_table = "df_address"

class TestModel(models.Model):
    """测试"""
    order_choices = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评论'),
        (5, '已完成'),
    )
    name = models.CharField(max_length=20, null=True)
    # 富文本控件
    desc = HTMLField(verbose_name='商品描述', null=True)
    status = models.IntegerField(choices=order_choices, verbose_name='订单详情', default=1)

    class Meta:
        verbose_name_plural = '测试'
