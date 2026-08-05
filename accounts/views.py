from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, SignUpForm


def _after_auth_redirect(user):
    if not user.profile_completed:
        return redirect("accounts:profile_setup")
    return redirect("trips:list")


def login_view(request):
    if request.user.is_authenticated:
        return _after_auth_redirect(request.user)

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return _after_auth_redirect(form.get_user())

    return render(request, "accounts/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        return _after_auth_redirect(request.user)

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "회원가입이 완료되었습니다. 프로필을 입력해 주세요.")
        return redirect("accounts:profile_setup")

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_setup_view(request):
    if request.user.profile_completed:
        return redirect("accounts:profile")

    form = ProfileForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        messages.success(request, "프로필이 저장되었습니다.")
        return redirect("trips:list")

    return render(request, "accounts/profile_setup.html", {"form": form})


@login_required
def profile_view(request):
    if not request.user.profile_completed:
        return redirect("accounts:profile_setup")

    completed_trips = request.user.trips.filter(status="done", result__isnull=False)
    total_trips = completed_trips.count()
    avg_disruption = None
    slowest_component = None

    if total_trips:
        scores = [trip.result.disruption_score for trip in completed_trips.select_related("result")]
        avg_disruption = round(sum(scores) / len(scores), 1)

    context = {
        "profile": request.user.profile,
        "total_trips": total_trips,
        "avg_disruption": avg_disruption,
        "slowest_component": slowest_component,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit_view(request):
    if not request.user.profile_completed:
        return redirect("accounts:profile_setup")

    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "프로필이 수정되었습니다.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def settings_view(request):
    return render(request, "accounts/settings.html")


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "로그아웃되었습니다.")
    return redirect("accounts:login")


@login_required
@require_POST
def delete_account_view(request):
    user = request.user
    logout(request)
    user.delete()
    messages.info(request, "계정과 관련 데이터가 삭제되었습니다.")
    return redirect("accounts:login")

# Create your views here.
