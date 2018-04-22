
from django.conf.urls import include, url
from django.contrib import admin

from apps.users import views

urlpatterns = [
    # http://127.0.0.1:8000/users/register
    # url(r'^register$', views.register, name='register'),
    # url(r'^do_register$', views.do_register, name='do_register'),

    url(r'^register$', views.RegisterView.as_view(), name='register'),

    # http://127.0.0.1:8000/users/active/eyJhbGciOiJIUzI1NiIsImlhdCI6MTUyNDMwMTQ1MiwiZXhwIjoxNTI0Mzg3ODUyfQ.eyJjb25maXJtIjoxNH0.LyqYBADhhKsoK8pPFi66PesPAF-P-bZKtCb_DolxeOI
    url(r'^active/(.+)$', views.ActiveView.as_view(), name='active'),

    # 127.0.0.1:8000/users/login
    url(r'^login$', views.LoginView.as_view(), name='login'),

    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^address$', views.UserAddressView.as_view(), name='address'),
    url(r'^orders$', views.UserOrderView.as_view(), name='orders'),
    url(r'^$', views.UserInfoView.as_view(), name='info'),


]
