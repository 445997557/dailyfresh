from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
from redis.client import StrictRedis

from apps.goods.models import GoodsSKU
from utils.commont import LoginRequiredMixin


class AddCartView(View):
    """添加到购物车"""

    def post(self, request):

        # 判断用户是否登陆
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登陆'})

        # 接收数据：user_id，sku_id，count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验参数all()

        if not all([sku_id, count]):
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})

        # 判断商品是否存在
        sku = None
        try:
            sku = GoodsSKU.objects.filter(id=sku_id)[0]
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 3, 'errmsg': '没有次商品'})


        # 判断count是否是整数

        try:
            count = int(count)
        except:
            return JsonResponse({'code': 4, 'errmsg': '数量需为整数'})

        # 判断库存
        strict_redis = get_redis_connection() # type: StrictRedis
        key = 'cart_{}'.format(request.user.id)
        val = strict_redis.hget(key, sku_id)
        if val:
            count += int(val)
        if sku.stock < count:
            return JsonResponse({'code': 5, 'errmsg': '库存不够'})

        # 操作redis数据库存储商品到购物车

        strict_redis.hset(key, sku_id, count)

        # 查询购物车中商品的总数量
        total_count = 0
        vals = strict_redis.hvals(key)
        for val in vals:
            total_count += int(val)

        # json方式响应添加购物车结果
        return JsonResponse({'code': 0, 'total_count': total_count})


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user_id = request.user.id
        skus = []
        total_count = 0
        total_amount = 0
        key = 'cart_{}'.format(user_id)
        strict_redis = get_redis_connection() # type: StrictRedis
        sku_ids = strict_redis.hkeys(key)
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=int(sku_id))
            count = int(strict_redis.hget(key, sku_id))
            amount = count * sku.price
            sku.count = count
            sku.amount = amount
            skus.append(sku)
            total_count += count
            total_amount += amount

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
        }
        return render(request, 'cart.html', context)


class CartUpdateView(View):
    def post(self, request):
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请登陆'})
        if not all([sku_id, count]):
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 3, 'errmsg': '商品不存在'})
        try:
            count = int(count)
        except:
            return JsonResponse({'code': 4, 'errmsg': '参数需为整数'})
        if count > sku.stock:
            return JsonResponse({'code': 5, 'errmsg': '库存不够'})
        strict_redis = get_redis_connection() # type: StrictRedis
        key = 'cart_{}'.format(request.user.id)
        strict_redis.hset(key, sku_id, count)
        # 查询购物车中商品的总数量
        total_count = 0
        vals = strict_redis.hvals(key)
        for val in vals:
            total_count += int(val)

        # json方式响应添加购物车结果
        return JsonResponse({'code': 0, 'total_count': total_count})


class CartDeleteView(View):
    def post(self, request):
        sku_id = request.POST.get('sku_id')
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请登陆'})
        if not sku_id:
            return JsonResponse({'code': 2, 'errmsg': '商品id不能为空'})
        strict_redis = get_redis_connection() # type: StrictRedis
        key = 'cart_{}'.format(request.user.id)
        strict_redis.hdel(key, sku_id)

        # 查询购物车中商品的总数量
        total_count = 0
        vals = strict_redis.hvals(key)
        for val in vals:
            total_count += int(val)

        # json方式响应添加购物车结果
        return JsonResponse({'code': 0, 'total_count': total_count})