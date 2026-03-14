from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.contrib.auth.forms import PasswordChangeForm

from .forms import *
from .models import *
from django.views.decorators.clickjacking import xframe_options_exempt


def home(request):
    return render(request, 'tracker/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})


@login_required
def dashboard(request):
    selected_date = request.GET.get('date') or date.today().isoformat()
    records = MealRecord.objects.filter(user=request.user, record_date=selected_date).select_related('food')

    totals = {
        'calories': round(sum(r.total_calories for r in records), 2),
        'protein': round(sum(r.total_protein for r in records), 2),
        'fat': round(sum(r.total_fat for r in records), 2),
        'carbohydrates': round(sum(r.total_carbohydrates for r in records), 2),
        'fiber': round(sum(r.total_fiber for r in records), 2),
    }

    recent_records = MealRecord.objects.filter(user=request.user).select_related('food')[:8]
    food_count = Food.objects.filter(user=request.user).count()
    record_count = MealRecord.objects.filter(user=request.user).count()

    context = {
        'selected_date': selected_date,
        'records': records,
        'totals': totals,
        'recent_records': recent_records,
        'food_count': food_count,
        'record_count': record_count,
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
def food_list(request):
    foods = Food.objects.filter(user=request.user)
    return render(request, 'tracker/food_list.html', {'foods': foods})


@login_required
def record_list(request):
    records = MealRecord.objects.filter(user=request.user).select_related('food')
    totals = {
        'calories': round(sum(r.total_calories for r in records), 2),
        'protein': round(sum(r.total_protein for r in records), 2),
        'fat': round(sum(r.total_fat for r in records), 2),
        'carbohydrates': round(sum(r.total_carbohydrates for r in records), 2),
        'fiber': round(sum(r.total_fiber for r in records), 2),
    }
    record_count = MealRecord.objects.filter(user=request.user).count()
    context = {
        'records': records,
        'totals': totals,
        'record_count': record_count,
    }
    
    return render(request, 'tracker/record_list.html', context)


@login_required
@xframe_options_exempt
def analysis_page(request):
    return render(request, 'tracker/analysis.html')


@login_required
def account_view(request):
    context = {
        "profile_form": ProfileUpdateForm(instance=request.user),
        "password_form": CustomPasswordChangeForm(user=request.user),
        "delete_form": DeleteAccountForm(user=request.user),
    }
    return render(request, "tracker/account.html", context)


def staff_required(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(staff_required)
def staff_required(user):
    return user.is_authenticated and user.is_staff