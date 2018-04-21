
from django.conf.urls import include, url
from django.contrib import admin

from apps.users import views

urlpatterns = [
    # http://127.0.0.1:8000/users/register
    url(r'^register$', views.register, name='register'),
    url(r'^do_register$', views.do_register, name='do_register'),
    # 127.0.0.1:8000/users/login
    url(r'^login$', views.login, name='login'),

]
