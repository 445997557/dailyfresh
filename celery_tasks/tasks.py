from celery import Celery
from django.core.mail import send_mail
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
