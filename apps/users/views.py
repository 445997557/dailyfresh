from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
import re

from apps.users.models import User


def register(request):
    context = {}
    return render(request, 'register.html', context)


def do_register(request):
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
        User.objects.create_user(username=username,
                                 password=password,
                                 email=email)
    except IntegrityError:
        context = {'text': '用户已经存在'}
        return render(request, 'register.html', context)
    request.session['username'] = username
    request.session['password'] = password
    return render(request, 'login.html')


def login(request):
    return render(request, 'login.html')