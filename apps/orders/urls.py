
from django.conf.urls import include, url
from django.contrib import admin

from apps.orders import views

urlpatterns = [
    url(r'^place$', views.PlaceOrdersView.as_view(), name='place'),
    # orders/commit
    url(r'^commit$', views.CommitOrdersView.as_view(), name='commit'),
]
