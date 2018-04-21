from django.contrib import admin

from apps.users.models import TestModel, User


class test(admin.ModelAdmin):
    list_display = ['id', 'name', 'desc', 'status']


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email']


admin.site.register(TestModel, test)
admin.site.register(User, UserAdmin)
