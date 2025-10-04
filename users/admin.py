from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser as User
from users.models import Driver


class UserAdmin(UserAdmin):
    search_fields = ['email', 'first_name', 'last_name']
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_master_user']
    list_filter = ['role', 'is_master_user']
    readonly_fields = ['id', 'date_joined', 'last_login']
    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_master_user')}),
        ('Organisation', {'fields': ('organisation',)}),
        ('System Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),)
    ordering = ['-id']


admin.site.register(User, UserAdmin)
admin.site.register(Driver)
