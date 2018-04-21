from django.core.mail import send_mail
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
import re

from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired

from apps.users.models import User

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


def login(request):
    return render(request, 'login.html')


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
