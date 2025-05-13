from django.contrib import admin
from users.models import UserProfile
# Import the custom admin site
from equipment.admin import admin_site
# Import User and UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register User model with the custom admin site using the standard UserAdmin
admin_site.register(User, BaseUserAdmin)

# Register your models here.
# Register with the custom admin site instead of the default
@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'experience_level')
    list_filter = ('user_type', 'experience_level')
    search_fields = ('user__username', 'phone_number')
