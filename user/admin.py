from django.contrib import admin

from .models import User, RefreshToken, Settings


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'username', 'password')


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency')


class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'created_time', 'end_time', 'user')


admin.site.register(User, UserAdmin)
admin.site.register(Settings, SettingsAdmin)
admin.site.register(RefreshToken, RefreshTokenAdmin)
