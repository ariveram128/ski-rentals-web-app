from django.shortcuts import redirect

#just to redirect from / to the actual login.
def home_redirect(request):
    return redirect('/equipment/')