"""
URL configuration for skirentals project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from users.views import (
    home, logout_view, role_based_redirect, 
    librarian_view, patron_view, cart_view, 
    help_view, edit_profile_view, profile_view,
    manage_users_view, promote_to_librarian, demote_to_patron
)

# Import custom admin site
from equipment.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),  # Use our custom admin site
    # path('admin/', admin.site.urls),  # Comment out the default admin site
    path('', home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('logout/', logout_view, name='logout'),
    path('dashboard_redirect/', role_based_redirect, name='dashboard_redirect'),
    path('librarian/', librarian_view, name='librarian'),
    path('patron/', patron_view, name='patron'),
    path('cart/', cart_view, name='cart'),
    path('help/', help_view, name='help'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('profile/', profile_view, name='profile'),
    path('manage-users/', manage_users_view, name='manage_users'),
    path('promote-to-librarian/<int:user_id>/', promote_to_librarian, name='promote_to_librarian'),
    path('demote-to-patron/<int:user_id>/', demote_to_patron, name='demote_to_patron'),
    path('equipment/', include('equipment.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
