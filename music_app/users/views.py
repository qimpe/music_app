import typing

from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView

from . import services
from .forms import SignInForm, SignUpForm
from .models import User


# Create your views here.
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "users/sign_up.html"


class SignInView(LoginView):
    form_class = SignInForm
    template_name = "users/sign_in.html"
    redirect_authenticated_user = True


class SignOutview(LogoutView):
    """Переопределенный стандартный метод выхода."""


class UserDetailView(DetailView):
    """Личный кабинет пользователя."""

    model = User
    template_name = "users/user_detail.html"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        user = self.object
        context: dict[str, typing.Any] = super().get_context_data(**kwargs)
        context["artists"] = services.fetch_artists_by_user(user=user)
        context["user"] = user
        return context
