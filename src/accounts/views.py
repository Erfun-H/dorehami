from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm, SignUpForm


def _next_url(request):
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return ""


def _redirect_after_auth(request):
    return redirect(_next_url(request) or "home")


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return _redirect_after_auth(request)
    return render(
        request,
        "accounts/signup.html",
        {"form": form, "next": _next_url(request)},
    )


def login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.cleaned_data["user"])
        return _redirect_after_auth(request)
    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": _next_url(request)},
    )


@require_POST
def logout(request):
    auth_logout(request)
    return redirect("home")
