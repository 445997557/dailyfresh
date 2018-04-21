
from django.conf.urls import include, url
from django.contrib import admin

from apps.goods import views

urlpatterns = [
    url(r'^index$', views.index),
]
