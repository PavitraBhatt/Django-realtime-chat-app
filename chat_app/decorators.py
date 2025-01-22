from django.shortcuts import redirect
from django.contrib import messages

def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        print('reqyest', request.user.is_authenticated)
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to access this page.")
            return redirect('mobile_login')
        return view_func(request, *args, **kwargs)
    return wrapper
