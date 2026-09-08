"""View handlers for user registration, authentication, and profile management."""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import RegistrationForm, ProfileUpdateForm
from .models import CustomUser


def register_view(request):
    """Handle new user registration and automatic login upon success."""
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, f"Welcome {user.username}! Your account has been created."
            )
            return redirect("news:home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Handle user authentication and redirection to the requested page or home."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next", "news:home")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


def logout_view(request):
    """Log the user out of the current session."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    """Render the profile page for the currently authenticated user."""
    return render(request, "accounts/profile.html", {"user": request.user})


@login_required
def profile_edit(request):
    """Handle the updating of user profile information and profile pictures."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})
