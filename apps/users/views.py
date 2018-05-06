from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
import re

from django.views.generic import View
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired
from redis import StrictRedis

from apps.goods.models import GoodsSKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import User, Address

# def register(request):
#     context = {}
#     return render(request, 'register.html', context)
#
#
# def do_register(request):
#     # 获取请求参数
#     # 用户名, 密码, 确认密码, 邮箱, 勾选用户协议
#     username = request.POST.get('username')
#     password = request.POST.get('password')
#     password2 = request.POST.get('password2')
#     email = request.POST.get('email')
#     allow = request.POST.get('allow')
#     # 校验参数合法性
#     # 逻辑判断 0 0.0 '' None [] () {}  -> False
#     # all: 所有的变量都为True, all函数才返回True, 否则返回False
#     if not all([username, password, password2, email, allow]):
#         context = {'text': '参数不完整'}
#         # return redirect('/users/register', context)
#         return render(request, 'register.html', context)
#     # 判断两次输入的密码是否正确
#     if password != password2:
#         context = {'text': '两次输入不一致'}
#         return render(request, 'register.html', context)
#     # 判断是否勾选了用户协议
#     if allow != 'on':
#         context = {'text': '请先同意用户协议'}
#         return render(request, 'register.html', context)
#     # 判断邮箱格式是否正确
#     if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#         context = {'text': '邮箱格式不正确'}
#         return render(request, 'register.html', context)
#     # 业务处理
#     # 保存用户到数据库中
#     # create_user: 是django提供的方法, 会对密码进行加密后再保存到数据库
#     try:
#         user = User.objects.create_user(username=username,
#                                  password=password,
#                                  email=email)
#         user.is_active = False
#         user.save()
#     except IntegrityError:
#         context = {'text': '用户已经存在'}
#         return render(request, 'register.html', context)
#     request.session['username'] = username
#     request.session['password'] = password
#     return render(request, 'login.html')
from celery_tasks.tasks import send_active_mail
from dailyfresh import settings

#
#
# def login(request):
#     return render(request, 'login.html')
from utils.commont import LoginRequiredMixin


class RegisterView(View):
    def get(self, request):
        context = {}
        return render(request, 'register.html', context)

    def post(self, request):
        # 获取请求参数
        # 用户名, 密码, 确认密码, 邮箱, 勾选用户协议
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 校验参数合法性
        # 逻辑判断 0 0.0 '' None [] () {}  -> False
        # all: 所有的变量都为True, all函数才返回True, 否则返回False
        if not all([username, password, password2, email, allow]):
            context = {'text': '参数不完整'}
            # return redirect('/users/register', context)
            return render(request, 'register.html', context)
        # 判断两次输入的密码是否正确
        if password != password2:
            context = {'text': '两次输入不一致'}
            return render(request, 'register.html', context)
        # 判断是否勾选了用户协议
        if allow != 'on':
            context = {'text': '请先同意用户协议'}
            return render(request, 'register.html', context)
        # 判断邮箱格式是否正确
        if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            context = {'text': '邮箱格式不正确'}
            return render(request, 'register.html', context)
        # 业务处理
        # 保存用户到数据库中
        # create_user: 是django提供的方法, 会对密码进行加密后再保存到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            email=email)  # type: User
            user.is_active = False
            user.save()
        except IntegrityError:
            context = {'text': '用户已经存在'}
            return render(request, 'register.html', context)
        token = user.generate_active_token()
        # RegisterView.send_active_mail(username, email, token)
        send_active_mail.delay(username, email, token)
        request.session['username'] = username
        request.session['password'] = password
        return render(request, 'login.html')

    @staticmethod
    def send_active_mail(username, email, token):

        subject = '天天生鲜，激活邮件'  # 标题，必须填写
        message = ''  # 正文
        from_email = settings.EMAIL_FROM  # 发件人
        recipient_list = [email]  # 收件人
        html_message = '<h2>尊敬的 %s, 感谢注册天天生鲜</h2>' \
                       '<p>请点击此链接激活您的帐号: '' \
                       ''<a href="http://127.0.0.1:8000/users/active/%s">'' \
                       ''http://127.0.0.1:8000/users/active/%s</a>' \
                       % (username, token, token)
        send_mail(subject=subject,
                  message=message,
                  from_email=from_email,
                  recipient_list=recipient_list,
                  html_message=html_message)


class ActiveView(View):
    def get(self, request, token: str):
        try:
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)
            dict_date = s.loads(token.encode())
        except SignatureExpired:
            return HttpResponse('激活链接已经失效')
        user_id = dict_date.get('confirm')
        User.objects.filter(id=user_id).update(is_active=True)
        return HttpResponse('激活成功')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        if not all([username, password]):
            context = {'errmsg': '用户名或密码不能为空'}
            return render(request, 'login.html', context)
        user = authenticate(username=username, password=password)
        if user is None:
            context = {'errmsg': '用户名或密码错误'}
            return render(request, 'login.html', context)
        if not user.is_active:
            context = {'errmsg': '用户未激活'}
            return render(request, 'login.html', context)

        login(request, user)
        if remember != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        next = request.GET.get('next')
        if next:
            if next == '/orders/place':
                return redirect('/cart')
            return redirect(next)
        else:
            return redirect(reverse('goods:index'))


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    """用户中心:个人信息界面"""

    def get(self, request):
        strict_redis = get_redis_connection('default')  # type: StrictRedis
        key = 'history_%s' % request.user.id
        sku_ids = strict_redis.lrange(key, 0, 4)
        # skus = GoodsSKU.objects.filter(id__in=sku_id)
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)

        try:
            address = request.user.address_set.latest('create_time')
        except Exception as e:
            address = None
            print(e)
        context = {
            'which_page': 1,
            'address': address,
            'skus': skus
        }
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    """用户中心--订单显示界面"""

    def get(self, request, page_no):

        orders = OrderInfo.objects.filter(user=request.user).order_by('-create_time')
        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order)
            for order_sku in order_skus:
                order_sku.amount = order_sku.price * order_sku.count
            order.status_desc = OrderInfo.ORDER_STATUS.get(order.status)
            order.total_pay = order.trans_cost + order.total_amount
            order.order_skus = order_skus

        paginator = Paginator(orders, 2)
        try:
            page = paginator.page(page_no)
        except EmptyPage:
            page = paginator.page(1)
        # if not request.user.is_authenticated():
        #     return redirect(reverse('users:login'))
        context = {
            'which_page': 2,
            'page': page,
            'page_range': paginator.page_range,

        }
        return render(request, 'user_center_order.html', context)


class UserAddressView(LoginRequiredMixin, View):
    """用户中心--地址界面"""

    def get(self, request):
        try:
            address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
        except:
            address = None
        context = {
            'which_page': 3,
            'address': address
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        receiver = request.POST.get('receiver')
        detail = request.POST.get('detail')
        zip_code = request.POST.get('zip_code')
        mobile = request.POST.get('mobile')
        if not all([receiver, detail, mobile]):
            return render(request, 'user_center_site.html', {'errmsg': '参数不能为空'})
        Address.objects.create(
            receiver_name=receiver,
            receiver_mobile=mobile,
            detail_addr=detail,
            zip_code=zip_code,
            user=request.user
        )
        return redirect(reverse('users:address'))

        # @login_required
        # def address(request):
        #     context = {
        #         'which_page': 3
        #     }
        #     return render(request, 'user_center_site.html', context)
