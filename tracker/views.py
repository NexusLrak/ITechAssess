from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Count

from .forms import *
from .models import *
from django.views.decorators.clickjacking import xframe_options_exempt


def home(request):
    if request.user.is_staff:
        return redirect('admin_user_list')
    elif request.user.is_authenticated:
        return redirect('dashboard')
    else :
        return render(request, 'tracker/login.html')



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

    records = MealRecord.objects.filter(
        user=request.user,
        record_date=selected_date
    )

    meal_data = (
        MealRecord.objects
        .filter(user=request.user, record_date=selected_date)
        .values("meal_type")
        .annotate(
            protein=Sum(
                ExpressionWrapper(F("food_protein") * F("quantity"), output_field=FloatField())
            ),
            fat=Sum(
                ExpressionWrapper(F("food_fat") * F("quantity"), output_field=FloatField())
            ),
            carbs=Sum(
                ExpressionWrapper(F("food_carbohydrates") * F("quantity"), output_field=FloatField())
            ),
            fibre=Sum(
                ExpressionWrapper(F("food_fiber") * F("quantity"), output_field=FloatField())
            ),
            calories=Sum(
                ExpressionWrapper(F("food_calories") * F("quantity"), output_field=FloatField())
            ),
        )
    )

    meal_summary = {
        "breakfast": {"protein": 0, "fat": 0, "carbs": 0, "fibre": 0, "calories": 0},
        "lunch": {"protein": 0, "fat": 0, "carbs": 0, "fibre": 0, "calories": 0},
        "dinner": {"protein": 0, "fat": 0, "carbs": 0, "fibre": 0, "calories": 0},
        "others": {"protein": 0, "fat": 0, "carbs": 0, "fibre": 0, "calories": 0},
    }

    for m in meal_data:
        meal = m["meal_type"]
        if meal == "snack":
            meal = "others"

        meal_summary[meal]["protein"] = round(m["protein"] or 0, 1)
        meal_summary[meal]["fat"] = round(m["fat"] or 0, 1)
        meal_summary[meal]["carbs"] = round(m["carbs"] or 0, 1)
        meal_summary[meal]["fibre"] = round(m["fibre"] or 0, 1)
        meal_summary[meal]["calories"] = round(m["calories"] or 0, 0)

    totals = {
        'calories': round(sum(r.total_calories for r in records), 2),
        'protein': round(sum(r.total_protein for r in records), 2),
        'fat': round(sum(r.total_fat for r in records), 2),
        'carbohydrates': round(sum(r.total_carbohydrates for r in records), 2),
        'fiber': round(sum(r.total_fiber for r in records), 2),
    }

    recent_activities = Activities.objects.filter(user=request.user)[:8]
    record_count = MealRecord.objects.filter(user=request.user).count()

    context = {
        'selected_date': selected_date,
        'meal_summary': meal_summary,
        'records': records,
        'totals': totals,
        'recent_activities': recent_activities,
        'record_count': record_count,
    }
    return render(request, 'tracker/dashboard.html', context)

from django.db.models import Q, Case, When, Value, IntegerField
@login_required
def food_list(request):
    foods = Food.objects.filter(user=request.user)

    admin_user = User.objects.filter(is_superuser=True).first()
    if(admin_user):
        foods = Food.objects.filter(
            Q(user=request.user) | Q(user=admin_user)
        ).annotate(
            sort_priority=Case(
                When(user=request.user, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('-id')

    return render(request, 'tracker/food_list.html', {'foods': foods})


@login_required
def record_list(request):
    date_list = (
        MealRecord.objects
        .filter(user=request.user)
        .values('record_date')
        .annotate(
            record_count=Count('id'),
            calories=Sum(F('food_calories') * F('quantity')),
            protein=Sum(F('food_protein') * F('quantity')),
            fat=Sum(F('food_fat') * F('quantity')),
            carbohydrates=Sum(F('food_carbohydrates') * F('quantity')),
            fiber=Sum(F('food_fiber') * F('quantity')),
        )
        .order_by('-record_date')
    )

    context = {
        'date_list': date_list
    }
    return render(request, 'tracker/record_list.html', context)


@login_required
def record_day_detail(request, record_date):
    records = (
        MealRecord.objects
        .filter(user=request.user, record_date=record_date)
        .order_by('meal_type', 'id')
    )

    day_totals = records.aggregate(
        calories=Sum(F('food_calories') * F('quantity')),
        protein=Sum(F('food_protein') * F('quantity')),
        fat=Sum(F('food_fat') * F('quantity')),
        carbohydrates=Sum(F('food_carbohydrates') * F('quantity')),
        fiber=Sum(F('food_fiber') * F('quantity')),
        count=Count('id'),
    )

    context = {
        'record_date': record_date,
        'records': records,
        'totals': {
            'calories': round(day_totals['calories'] or 0, 2),
            'protein': round(day_totals['protein'] or 0, 2),
            'fat': round(day_totals['fat'] or 0, 2),
            'carbohydrates': round(day_totals['carbohydrates'] or 0, 2),
            'fiber': round(day_totals['fiber'] or 0, 2),
            'count': day_totals['count'] or 0,
        }
    }
    return render(request, 'tracker/record_day_detail.html', context)


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
