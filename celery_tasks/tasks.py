# import os
# import django
# # 设置环境变量
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# # 初始化django环境
# django.setup()
from time import sleep

from celery import Celery
from django.core.mail import send_mail
from django.template import loader
from apps.goods.models import *
from dailyfresh import settings


app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/1')


@app.task
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


@app.task
def generate_static_index_page():
    sleep(2)
    categories = GoodsCategory.objects.all()
    slide_skus = IndexSlideGoods.objects.all().order_by('index')
    promotions = IndexPromotion.objects.all().order_by('index')[0:2]
    for c in categories:
        text_skus = IndexCategoryGoods.objects.filter(display_type=0, category=c)
        image_skus = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
        c.text_skus = text_skus
        c.image_skus = image_skus

    cart_count = 0

    context = {
        'categories': categories,
        'slide_skus': slide_skus,
        'promotions': promotions,
        'cart_count': cart_count
    }
    template = loader.get_template('index.html')
    html_str = template.render(context)
    path = '/home/python/Documents/static/index.html'
    with open(path, 'w') as file:
        file.write(html_str)