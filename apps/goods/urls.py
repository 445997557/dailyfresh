
from django.conf.urls import include, url
from django.contrib import admin

from apps.goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index'),
    # http://127.0.0.1:8000/detail/商品id
    url(r'^detail/(\d+)$', views.DetailView.as_view(), name='detail'),
]
