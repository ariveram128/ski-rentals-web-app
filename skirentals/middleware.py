from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            # List of allowed paths and patterns
            admin_paths = ['/admin/', '/static/', '/media/']
            logout_patterns = ['/accounts/logout/', '/accounts/login/', '/logout/']

            # Check if path is allowed
            is_admin_path = any(request.path.startswith(path) for path in admin_paths)
            is_logout = any(request.path.startswith(path) for path in logout_patterns)

            # Allow admin paths and logout, redirect others to admin
            if not is_admin_path and not is_logout:
                return redirect('admin:index')
        
        response = self.get_response(request)
        return response

class OAuthCancelledMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a cancelled OAuth request
        if request.path in ['/accounts/3rdparty/login/cancelled/',
                            '/accounts/social/login/cancelled/',
                            '/accounts/login/cancelled/']:
            messages.info(request, "Login was cancelled. Please try again if you want to access the site.")
            return redirect('home')

        response = self.get_response(request)
        return response

class AccountCleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a cancelled OAuth request
        if request.path in ['/accounts/email/',
                            '/accounts',
                            '/accounts/password/set/',
                            '/accounts/password/reset/',
                            '/accounts/password/reset/done/',
                            '/accounts/password/change/',
                            '/accounts/password/change/done/',
                            'accounts/3rdparty/login/error/'
                            '/accounts/3rdparty/'
                            '/accounts/logout/',
                            '/accounts/social/',
                            '/accounts/inactive/',
                            '/accounts/confirm-email/'
                            ]:
            messages.info(request, "Redirect access to old account site to main site")
            return redirect('home')

        response = self.get_response(request)
        return response