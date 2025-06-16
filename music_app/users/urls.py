from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("sign-up/", views.SignUpView.as_view(), name="sign_up"),
    path("sign-in/", views.SignInView.as_view(), name="sign_in"),
    path("sign-out/", views.SignOutView.as_view(), name="sign_out"),
    path("profile/<int:pk>/", views.UserDetailView.as_view(), name="profile"),
]
