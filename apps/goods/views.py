from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
from django_redis import get_redis_connection
from redis import StrictRedis

from apps.goods.models import *


class BaseCartView(View):
    def get_cart_count(self, request):
        cart_count = 0
        if request.user.is_authenticated():
            strict_redis = get_redis_connection() # type:StrictRedis
            key = 'cart_{}'.format(request.user.id)
            vals = strict_redis.hvals(key)
            for count in vals:
                cart_count += int(count)
        return cart_count


class IndexView(BaseCartView):
    def get(self, request):
        categories = GoodsCategory.objects.all()
        slide_skus = IndexSlideGoods.objects.all().order_by('index')
        promotions = IndexPromotion.objects.all().order_by('index')[0:2]
        for c in categories:
            text_skus = IndexCategoryGoods.objects.filter(display_type=0, category=c)
            image_skus = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
            c.text_skus = text_skus
            c.image_skus = image_skus

        cart_count = self.get_cart_count(request)

        context = {
            'categories': categories,
            'slide_skus': slide_skus,
            'promotions': promotions,
            'cart_count': cart_count
        }
        return render(request, 'index.html', context)
