from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
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
        key = '_{}'.format(request.user.id)
        context = cache.get('index_page_date')
        if not context:
            print('没有缓存')
            categories = GoodsCategory.objects.all()
            slide_skus = IndexSlideGoods.objects.all().order_by('index')
            promotions = IndexPromotion.objects.all().order_by('index')[0:2]
            for c in categories:
                text_skus = IndexCategoryGoods.objects.filter(display_type=0, category=c)
                image_skus = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
                c.text_skus = text_skus
                c.image_skus = image_skus
            context = {
                'categories': categories,
                'slide_skus': slide_skus,
                'promotions': promotions,
            }
            cache.set('index_page_date', context, 60*30)
        else:
            print('有缓存')
            # 获取购物车中的商品数量
            cart_count = self.get_cart_count(request)
            context['cart_count'] = cart_count

        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    def get(self, request, sku_id):
        # 查询商品详情信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 查询不到商品则跳转到首页
            return redirect(reverse('goods:index'))

        # 获取所有的类别数据
        categories = GoodsCategory.objects.all()
        # 获取最新推荐
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[0:2]
        # 获取购物车中的商品数量
        cart_count = self.get_cart_count(request)

        # 查询其它规格的商品
        # other_skus = sku.spu.goodssku_set.exclude(id=sku)
        other_skus = GoodsSKU.objects.filter(spu=sku.spu).exclude(id=sku_id)

        # 如果是登录的用户
        if request.user.is_authenticated:
            # 获取用户id
            user_id = request.user.id
            # 从redis中获取购物车信息/获取StrictRedis对象
            # redis_conn = StrictRedis()
            redis_conn = get_redis_connection() # type: StrictRedis
            # 保存用户的历史浏览记录
            # history_用户id: [3, 1, 2]
            # 移除现有的商品浏览记录
            key = 'history_{}'.format(user_id)
            redis_conn.lrem(key, 0, sku_id)
            # 从左侧添加新的商品浏览记录
            redis_conn.lpush(key, sku_id)
            # 控制历史浏览记录最多只保存5项(包含头尾)
            redis_conn.ltrim(key, 0, 4)
            context = {
                'categories': categories,
                'sku': sku,
                'new_skus': new_skus,
                'other_skus': other_skus,
                'cart_count': cart_count,
            }
            return render(request, 'detai.html', context)