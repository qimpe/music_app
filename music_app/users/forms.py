from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")


class SignInForm(AuthenticationForm):
    pass
