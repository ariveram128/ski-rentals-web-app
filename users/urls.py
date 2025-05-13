from django.urls import path
from . import views
from .views import role_based_redirect

urlpatterns = [
    path("", views.home, name="home"),
    path("logout", views.logout_view, name="logout"),
    path('home/', role_based_redirect, name="dashboard_redirect"),
    path('librarian/', views.librarian_view, name="librarian"),
    path('patron/', views.patron_view, name="patron"),
    path('cart/', views.cart_view, name="cart"),
    path('help/', views.help_view, name="help"),
    path('edit-profile/', views.edit_profile_view, name="edit_profile"),
    path('profile/', views.profile_view, name="profile"),
    path('manage-users/', views.manage_users_view, name="manage_users"),
    path('promote-to-librarian/<int:user_id>/', views.promote_to_librarian, name="promote_to_librarian"),
    path('demote-to-patron/<int:user_id>/', views.demote_to_patron, name="demote_to_patron"),
]