from django.contrib import admin
from django.utils.html import format_html
from .models import Collection, Equipment, MaintenanceRecord, Rental, Review, Cart, CartItem, EquipmentImage
# Import models for Sites and Social Accounts
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken

# Custom AdminSite class
class SkiRentalsAdminSite(admin.AdminSite):
    site_title = "SkiRentals Admin"
    site_header = "SkiRentals Administration"
    index_title = "Equipment Management Dashboard"
    
# Initialize the custom admin site
admin_site = SkiRentalsAdminSite(name='skirentalsadmin')

# Equipment image inline with preview
class EquipmentImageInline(admin.TabularInline):
    model = EquipmentImage
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "No Image"
    
    image_preview.short_description = "Preview"

@admin.register(Equipment, site=admin_site)
class EquipmentAdmin(admin.ModelAdmin):
    inlines = [EquipmentImageInline]
    list_display = ('equipment_id', 'brand', 'model', 'equipment_type', 'condition', 'is_available', 'image_thumbnail')
    list_filter = ('equipment_type', 'condition', 'is_available', 'recommended_skill_level')
    search_fields = ('equipment_id', 'brand', 'model')
    
    def image_thumbnail(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="50" height="auto" />', obj.main_image.url)
        return "No Image"
    
    image_thumbnail.short_description = "Thumbnail"

@admin.register(MaintenanceRecord, site=admin_site)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'date_maintained', 'maintained_by', 'maintenance_type')
    list_filter = ('maintenance_type', 'date_maintained')

@admin.register(Rental, site=admin_site)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'patron', 'rental_status', 'checkout_date', 'due_date')
    list_filter = ('rental_status', 'rental_duration')
    search_fields = ('patron__username', 'equipment__equipment_id')

@admin.register(Review, site=admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'rating', 'date_posted')
    list_filter = ('rating', 'date_posted')

@admin.register(Collection, site=admin_site)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_public', 'created_date', 'modified_date')
    list_filter = ('is_public', 'created_date')
    search_fields = ('title', 'description')
    filter_horizontal = ('authorized_users',)

# Register the remaining models with the custom admin site
admin_site.register(Cart)
admin_site.register(CartItem)
admin_site.register(EquipmentImage)

# Register Site and Social Account models
admin_site.register(Site)
admin_site.register(SocialAccount)
admin_site.register(SocialApp)
admin_site.register(SocialToken)

# Also register with the default site for now 
# This will be disabled once we switch the URLs
# Keep the existing registrations to avoid errors until URL update