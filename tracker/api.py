from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout, update_session_auth_hash
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.http import JsonResponse, HttpResponse

from datetime import date, datetime, timedelta

from django.urls import reverse

from .forms import *
from .models import *

User = get_user_model()

def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        error = None

        # email format validation
        try:
            validate_email(email)
        except ValidationError:
            error = "Invalid email format."

        # username exists
        if not error and User.objects.filter(username=username).exists():
            error = "Username already exists."

        # email exists
        if not error and User.objects.filter(email=email).exists():
            error = "Email already registered."

        # password check
        if not error and password != password2:
            error = "Passwords do not match."

        # create user
        if not error:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            login(request, user)
            return redirect("/")

        return render(request, "tracker/register.html", {"error": error})

    return render(request, "tracker/register.html")



def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "tracker/login.html", {
                "error": "Invalid username or password."
            })

    return render(request, "tracker/login.html")



@login_required
def analysis(request):
    selected_date = request.GET.get("date")

    if selected_date:
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        selected_date = date.today()

    start_date = selected_date - timedelta(days=selected_date.weekday())
    end_date = start_date + timedelta(days=6)

    qs = MealRecord.objects.filter(
        user=request.user,
        record_date__range=(start_date, end_date)
    )

    calories_expr = ExpressionWrapper(
        F('food_calories') * F('quantity'),
        output_field=FloatField()
    )
    protein_g_expr = ExpressionWrapper(
        F('food_protein') * F('quantity'),
        output_field=FloatField()
    )
    carbs_g_expr = ExpressionWrapper(
        F('food_carbohydrates') * F('quantity'),
        output_field=FloatField()
    )
    fat_g_expr = ExpressionWrapper(
        F('food_fat') * F('quantity'),
        output_field=FloatField()
    )
    fibre_g_expr = ExpressionWrapper(
        F('food_fiber') * F('quantity'),
        output_field=FloatField()
    )

    # stacked bar cahrt aggregated by date
    daily_rows = (
        qs.values('record_date')
        .annotate(
            total_calories=Sum(calories_expr),
            protein_kcal=Sum(ExpressionWrapper(protein_g_expr * 4.0, output_field=FloatField())),
            carbs_kcal=Sum(ExpressionWrapper(carbs_g_expr * 4.0, output_field=FloatField())),
            fat_kcal=Sum(ExpressionWrapper(fat_g_expr * 9.0, output_field=FloatField())),
            fibre_kcal=Sum(ExpressionWrapper(fibre_g_expr * 2.0, output_field=FloatField())),
        )
        .order_by('record_date')
    )

    daily_stack_data = []
    for row in daily_rows:
        day = row["record_date"].isoformat()
        total_calories = round(row["total_calories"] or 0, 2)

        daily_stack_data.extend([
            {
                "date": day,
                "macro": "Protein",
                "kcal": round(row["protein_kcal"] or 0, 2),
                "dailyCalories": total_calories,
            },
            {
                "date": day,
                "macro": "Carbs",
                "kcal": round(row["carbs_kcal"] or 0, 2),
                "dailyCalories": total_calories,
            },
            {
                "date": day,
                "macro": "Fat",
                "kcal": round(row["fat_kcal"] or 0, 2),
                "dailyCalories": total_calories,
            },
        ])

    return JsonResponse({
        "barData": daily_stack_data
    })



@login_required
def food_create(request):
    if request.method == 'POST':
        form = FoodForm(request.POST)
        if form.is_valid():
            food = form.save(commit=False)

            admin_user = User.objects.filter(is_superuser=True).first()
            staff_users = User.objects.filter(is_staff=True)

            if (admin_user) and (request.user in staff_users):
                food.user = admin_user
            else:
                food.user = request.user

            food.save()

            Activities.objects.create(
                user=request.user,
                textinfo=f'Add a new food: "{food.name}".'
            )

            messages.success(request, 'Food added successfully.')
            return HttpResponse(status=204)

    else:
        form = FoodForm()

    return render(
        request,
        'tracker/food_form.html',
        {
            'form': form,
            'title': 'Add Food',
            'form_action': reverse('food_create')
        }
    )

@login_required
def food_edit(request, pk):
    food = get_object_or_404(Food, pk=pk, user=request.user)

    if request.method == 'POST':
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()

            messages.success(request, 'Food updated successfully.')
            return HttpResponse(status=204)
    else:
        form = FoodForm(instance=food)

    return render(
        request,
        'tracker/food_form.html',
        {
            'form': form,
            'title': 'Edit Food',
            'form_action': reverse('food_edit', args=[food.pk])
        }
    )

@login_required
def food_delete(request, pk):
    food = get_object_or_404(Food, pk=pk, user=request.user)

    if request.method == 'POST':
        food.delete()

        Activities.objects.create(
            user=request.user,
            textinfo=f'Delete a food: "{food.name}".'
        )

        messages.success(request, 'Food deleted successfully.')
        return HttpResponse(status=204)

    return render(
        request,
        'tracker/confirm.html',
        {
            'object': food,
            'type_name': 'food',
            'option': 'Delete',
            'form_action': reverse('food_delete', args=[food.pk])
        }
    )




@login_required
def record_create(request):
    if request.method == 'POST':
        form = MealRecordForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            
            Activities.objects.create(
                user=request.user,
                textinfo=f'Add a new record of date: {record.record_date}.'
            )

            messages.success(request, 'Meal record added successfully.')
            return HttpResponse(status=204)
    else:
        form = MealRecordForm(user=request.user, initial={'record_date': date.today()})

    return render(
        request,
        'tracker/record_form.html',
        {
            'form': form,
            'title': 'Add Record',
            'form_action': reverse('record_create')
        }
    )

@login_required
def record_edit(request, pk):
    record = get_object_or_404(MealRecord, pk=pk, user=request.user)

    if request.method == 'POST':
        form = MealRecordForm(request.POST, instance=record, user=request.user)

        if form.is_valid():
            form.save()

            messages.success(request, 'Meal record updated successfully.')
            return HttpResponse(status=204)

    else:
        form = MealRecordForm(instance=record, user=request.user)

    return render(
        request,
        'tracker/record_form.html',
        {
            'form': form,
            'title': 'Edit Record',
            'form_action': reverse('record_edit', args=[record.pk])
        }
    )


@login_required
def record_delete(request, pk):
    record = get_object_or_404(MealRecord, pk=pk, user=request.user)

    if request.method == 'POST':
        record.delete()

        messages.success(request, 'Meal record deleted successfully.')
        return HttpResponse(status=204)

    return render(
        request,
        'tracker/confirm.html',
        {
            'object': record,
            'type_name': 'record',
            'option': 'Delete',
            'form_action': reverse('record_delete', args=[record.pk])
        }
    )



@login_required
def update_profile_view(request):
    if request.method != "POST":
        return redirect("account")

    profile_form = ProfileUpdateForm(request.POST, instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    delete_form = DeleteAccountForm(user=request.user)

    if profile_form.is_valid():
        profile_form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("account")

    messages.error(request, "Please correct the profile form errors.")
    return render(
        request,
        "tracker/account.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "delete_form": delete_form,
        },
    )


@login_required
def change_password_view(request):
    if request.method != "POST":
        return redirect("account")

    profile_form = ProfileUpdateForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
    delete_form = DeleteAccountForm(user=request.user)

    if password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password updated successfully.")
        return redirect("account")

    messages.error(request, "Please correct the password form errors.")
    return render(
        request,
        "tracker/account.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "delete_form": delete_form,
        },
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("home")
    return redirect("account")


@login_required
def delete_account_view(request):
    if request.method != "POST":
        return redirect("account")

    profile_form = ProfileUpdateForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    delete_form = DeleteAccountForm(request.user, request.POST)

    if delete_form.is_valid():
        user = request.user
        logout(request)
        user.delete()
        return redirect("home")

    messages.error(request, "Account deletion failed.")
    return render(
        request,
        "tracker/account.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "delete_form": delete_form,
        },
    )