from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Profile, User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(
            attrs={
                "class": "field__input",
                "placeholder": "E-mail@email.com",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(
            attrs={
                "class": "field__input",
                "placeholder": "비밀번호",
                "autocomplete": "current-password",
            }
        ),
    )


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(
            attrs={
                "class": "field__input",
                "placeholder": "8자 이상",
                "autocomplete": "new-password",
            }
        ),
        help_text="8자 이상 입력해 주세요.",
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput(
            attrs={
                "class": "field__input",
                "placeholder": "8자 이상",
                "autocomplete": "new-password",
            }
        ),
    )
    terms_agreed = forms.BooleanField(
        label="개인정보 수집 및 이용에 동의합니다",
        widget=forms.CheckboxInput(attrs={"class": "auth-agree__input"}),
    )

    class Meta:
        model = User
        fields = ["email"]
        labels = {"email": "이메일"}
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "field__input",
                    "placeholder": "E-mail@email.com",
                    "autocomplete": "email",
                }
            )
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("이미 가입된 이메일입니다.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("비밀번호가 일치하지 않습니다.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password1")
        if password:
            password_validation.validate_password(password)
        return cleaned_data

    def save(self, commit=True):
        from django.utils import timezone

        user = super().save(commit=False)
        user.email = user.email.lower()
        user.set_password(self.cleaned_data["password1"])
        user.terms_agreed_at = timezone.now()
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    nickname = forms.CharField(
        label="닉네임",
        min_length=2,
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "field__input",
                "placeholder": "2자 이상",
                "autocomplete": "nickname",
            }
        ),
    )

    class Meta:
        model = Profile
        fields = ["nickname", "gender", "age"]
        labels = {
            "gender": "성별",
            "age": "나이",
        }
        widgets = {
            "gender": forms.RadioSelect,
            "age": forms.NumberInput(
                attrs={
                    "class": "field__input",
                    "placeholder": "입력",
                    "min": 1,
                    "max": 120,
                    "inputmode": "numeric",
                }
            ),
        }
