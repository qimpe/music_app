from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from music.models import Artist

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
    pass


class UserDetailView(DetailView):
    model = User
    template_name = "users/user_detail.html"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        user = self.object
        context = super().get_context_data(**kwargs)
        artists = Artist.objects.select_related("user").filter(user=user)
        context["artists"] = artists
        context["user"] = user
        return context
