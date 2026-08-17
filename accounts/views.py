from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordChangeDoneView as DjangoPasswordChangeDoneView
from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.contrib.auth.views import PasswordResetCompleteView as DjangoPasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView as DjangoPasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView as DjangoPasswordResetDoneView
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from accounts import selectors, services
from accounts.forms import UserCreateForm
from accounts.permissions import can_manage_users
from audit.models import AuditLogEntry
from audit.services import log_event
from common.ratelimit import rate_limit


@method_decorator(rate_limit("login", limit=settings.RATE_LIMIT_LOGIN_PER_MIN), name="post")
class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        # Redirect-after-failure (rather than re-rendering the bound form on
        # the POST response) so a browser refresh is just a harmless GET
        # instead of resubmitting the login POST and repeating the error.
        messages.error(self.request, "Please enter a correct username and password.")
        return redirect("accounts:login")


class LogoutView(DjangoLogoutView):
    next_page = "accounts:login"


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


class PasswordChangeView(DjangoPasswordChangeView):
    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        log_event(
            actor=self.request.user,
            action=AuditLogEntry.Action.PASSWORD_CHANGED,
            description=f"{self.request.user.username} changed their password",
            target=self.request.user,
        )
        return response


class PasswordChangeDoneView(DjangoPasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


@method_decorator(rate_limit("password_reset", limit=settings.RATE_LIMIT_PASSWORD_RESET_PER_MIN), name="post")
class PasswordResetView(DjangoPasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@login_required
def user_list(request):
    if not can_manage_users(request.user):
        raise PermissionDenied
    return render(request, "accounts/user_list.html", {"users": selectors.all_users()})


@login_required
def user_create(request):
    if not can_manage_users(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = services.create_user(form=form, created_by=request.user)
            messages.success(request, f"User “{user.username}” created.")
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form})
