from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField("이메일", unique=True)
    terms_agreed_at = models.DateTimeField("약관 동의 시각", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def profile_completed(self):
        return hasattr(self, "profile")


class Profile(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "female", "여성"
        MALE = "male", "남성"
        UNDISCLOSED = "undisclosed", "응답 안 함"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="사용자",
    )
    nickname = models.CharField("닉네임", max_length=10)
    gender = models.CharField("성별", max_length=20, choices=Gender.choices)
    age = models.PositiveSmallIntegerField("나이", validators=[MinValueValidator(1), MaxValueValidator(120)])
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)
    updated_at = models.DateTimeField("수정 시각", auto_now=True)

    class Meta:
        verbose_name = "프로필"
        verbose_name_plural = "프로필"

    def __str__(self):
        return f"{self.nickname} ({self.user.email})"

# Create your models here.
