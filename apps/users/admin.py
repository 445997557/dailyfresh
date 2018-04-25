from django.contrib import admin

from apps.goods.models import *
from apps.users.models import TestModel, User


class test(admin.ModelAdmin):
    list_display = ['id', 'name', 'desc', 'status']


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email']


admin.site.register(TestModel, test)
admin.site.register(User, UserAdmin)
admin.site.register(GoodsCategory)
admin.site.register(GoodsSPU)
admin.site.register(GoodsSKU)
admin.site.register(IndexSlideGoods)
admin.site.register(IndexPromotion)
admin.site.register(IndexCategoryGoods)
