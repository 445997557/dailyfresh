from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection
from redis.client import StrictRedis

from apps.goods.models import GoodsSKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.commont import LoginRequiredMixin


class PlaceOrdersView(LoginRequiredMixin, View):
    def post(self, request):

        # 获取请求参数：sku_ids，count
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')
        # 校验参数合法性

        if not sku_ids:
            return redirect(reverse('cart:info'))
        # todo: 查询业务数据： 地址，购物车商品，总数量，总金额
        # 获取用户地址信息
        # Address.objects.filter(user=request.user).order_by('-create_time')[0]
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except:
            address = None

        skus = []
        total_count = 0
        total_amount = 0
        strict_redis = get_redis_connection()  # type: StrictRedis
        key = 'cart_{}'.format(request.user.id)
        # 如果是从购物车页面过来，商品的数量从redis中获取

        if count is None:
            # 循环商品id： sku_ids
            for sku_id in sku_ids:
                # 查询商品对象
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))

                # 获取商品数量和小计金额(类型转换)
                count = strict_redis.hget(key, sku_id)
                count = int(count)
                amount = sku.price * count

                # 给商品对象新增实例属性(count, amount)
                sku.count = count
                sku.amount = amount

                # 添加商品对象到列表中
                skus.append(sku)
                # 累计商品总数量和总金额
                total_amount += amount
                total_count += count
        else:

            # 如果是从详情页面过来，商品的数量从request中获取（只有一个商品）
            sku_id = request.POST.get('sku_ids')
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('cart:info'))

            # 获取商品数量和小计金额(类型转换)
            count = int(count)
            amount = sku.price * count
            # 判断库存：详情页没有判断库存
            if count > sku.stock:
                return redirect(reverse('goods:detail', args=[sku_id]))

            # 给商品对象新增实例属性(count, amount)
            sku.count = count
            sku.amount = amount

            # 添加商品对象到列表中
            skus.append(sku)
            # 累计商品总数量和总金额
            total_amount += amount
            total_count += count
            # 将商品数量保存到`Redis`中（以便取消操作在购物车中还能看得到商品）\

            strict_redis.hset(key, sku_id, count)
        # 运费(固定)
        trans_cost = 10
        # 实付金额
        total_pay = total_amount + trans_cost

        # 定义模板显示的字典数据
        sku_ids_str = ','.join(sku_ids)
        context = {
            'skus': skus,
            'address': address,
            'total_count': total_count,
            'total_amount': total_amount,
            'trans_cost': trans_cost,
            'total_pay': total_pay,
            'sku_ids_str': sku_ids_str,
        }

        # 响应结果: 返回确认订单html界面

        return render(request, 'place_order.html', context)


class CommitOrdersView(View):
    @transaction.atomic
    def post(self, request):
        # 登录判断
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登陆'})
        # 获取请求参数：address_id, pay_method, sku_ids_str
        address_id = request.POST.get('address_id')
        pay_method = request.POST.get('pay_method')
        sku_ids_str = request.POST.get('sku_ids_str')

        # 校验参数不能为空
        if not all([address_id, pay_method, sku_ids_str]):
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})

        # 判断地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 3, 'errmsg': '地址不存在'})


        point = transaction.savepoint()
        try:
            # todo: 修改订单信息表: 保存订单数据到订单信息表中
            total_count = 0
            total_amount = 0
            trans_cost = 10
            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(request.user.id)
            order = OrderInfo.objects.create(
                order_id=order_id,
                total_count=total_count,
                total_amount=total_amount,
                trans_cost=trans_cost,
                pay_method=pay_method,
                user=request.user,
                address=address,
            )

            # 获取StrictRedis对象: cart_1 = {1: 2, 2: 2}
            strict_redis = get_redis_connection()  # type: StrictRedis
            key = 'cart_{}'.format(request.user.id)
            sku_ids = sku_ids_str.split(',')

            # todo: 核心业务: 遍历每一个商品, 并保存到订单商品表
            for sku_id in sku_ids:
                sku_id = int(sku_id)
                # 查询订单中的每一个商品对象
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(point)
                    return JsonResponse({'code': 4, 'errmsg': '商品不存在'})

                # 获取商品数量，并判断库存
                sku_count = int(strict_redis.hget(key, sku_id))
                if sku_count > sku.stock:
                    transaction.savepoint_rollback(point)
                    return JsonResponse({'code': 5, 'errmsg': '商品库存不足'})


                # todo: 修改订单商品表: 保存订单商品到订单商品表
                OrderGoods.objects.create(
                    count=sku_count,
                    price=sku.price,
                    order=order,
                    sku=sku,
                )

                # todo: 修改商品sku表: 减少商品库存, 增加商品销量
                sku.stock -= sku_count
                sku.sales += sku_count
                sku.save()
                # 累加商品数量和总金额
                total_count += sku_count
                total_amount += (sku_count * sku.price)

                # todo: 修改订单信息表: 修改商品总数量和总金额
            order.total_count = total_count
            order.total_amount = total_amount
            order.save()
        except:
            transaction.savepoint_rollback(point)
            return JsonResponse({'code': 6, 'errmsg': '下单失败'})

        transaction.savepoint_commit(point)

        # 从Redis中删除购物车中的商品
        # cart_1 = {1: 2, 2: 2}
        # redis命令: hdel cart_1 1 2
        strict_redis.hdel(key, *sku_ids)

        # 订单创建成功， 响应请求，返回json
        return JsonResponse({'code': 0, 'message': '下单成功'})
