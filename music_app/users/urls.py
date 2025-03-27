from django.urls import path

from .views import SignInView, SignOutview, SignUpView, UserDetailView

app_name = "users"

urlpatterns = [
    path("sign-up/", SignUpView.as_view(), name="sign_up"),
    path("sign-in/", SignInView.as_view(), name="sign_in"),
    path("sign-out/", SignOutview.as_view(), name="sign_out"),
    path("profile/<int:pk>/", UserDetailView.as_view(), name="profile"),
]
