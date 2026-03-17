from django.contrib import messages
from django.contrib.auth import get_user_model, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse

from .adminform import AdminUserUpdateForm
from .forms import Food, FoodForm
from .models import Activities

from .forms import (
    CustomPasswordChangeForm,
    DeleteAccountForm,
    ProfileUpdateForm,
)

User = get_user_model()

def staff_required(user):
    return user.is_authenticated and user.is_staff


@login_required
def account_view(request):
    context = {
        "profile_form": ProfileUpdateForm(instance=request.user),
        "password_form": CustomPasswordChangeForm(user=request.user),
        "delete_form": DeleteAccountForm(user=request.user),
    }
    return render(request, "tracker/account.html", context)


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


@login_required
@user_passes_test(staff_required)
def admin_user_list_view(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    users = User.objects.all().order_by("-date_joined")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)
    elif status == "staff":
        users = users.filter(is_staff=True)
    elif status == "superuser":
        users = users.filter(is_superuser=True)

    context = {
        "users": users,
        "query": query,
        "status": status,
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "staff_users": User.objects.filter(is_staff=True).count(),
    }
    return render(request, "tracker/adminpage.html", context)


@login_required
@user_passes_test(staff_required)
def admin_user_detail_view(request, user_id):
    managed_user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = AdminUserUpdateForm(request.POST, instance=managed_user)
        if form.is_valid():
            if user_id == request.user and not \
                (form.cleaned_data["is_superuser"] \
                 and form.cleaned_data["is_staff"] \
                 and form.cleaned_data["is_active"]):
                
                messages.error(request, "Cannot remove admin access.")
            elif  managed_user == request.user and not form.cleaned_data["is_staff"]:
                messages.error(request, "You cannot remove your own staff access.")
            else:
                form.cleaned_data["is_superuser"] = False
                form.save()
                messages.success(request, "User updated successfully.")
                return redirect("admin_user_detail", user_id=managed_user.id)
    else:
        form = AdminUserUpdateForm(instance=managed_user)

    context = {
        "managed_user": managed_user,
        "form": form,
    }
    return render(request, "tracker/adminuserdetail.html", context)


@login_required
@user_passes_test(staff_required)
def admin_user_delete_view(request, user_id):
    managed_user = get_object_or_404(User, pk=user_id)

    if request.method != "POST":
        return redirect("admin_user_detail", user_id=managed_user.id)

    if managed_user == request.user:
        messages.error(request, "You cannot delete your own account from the admin panel.")
        return redirect("admin_user_detail", user_id=managed_user.id)
    
    if user_id == 1:
            messages.error(request, "You cannot delete admin account from this panel.")
            return redirect("admin_user_detail", user_id=managed_user.id)

    managed_user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect("admin_user_list")


from django.db.models import Q, Case, When, Value, IntegerField
from django.urls import reverse

@login_required
@user_passes_test(staff_required)
def food_list_admin(request):
    admin_user = User.objects.filter(is_superuser=True).first()
    foods = Food.objects.all().annotate(
        sort_priority=Case(
            When(user=admin_user, then=Value(0)),
            When(user=request.user, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('sort_priority', '-id')

    return render(request, 'tracker/food_list.html', {'foods': foods})

@login_required
@user_passes_test(staff_required)
def food_adopt(request, pk):
    food = get_object_or_404(Food, pk=pk)

    
    if request.method == 'POST':
        admin_user = User.objects.filter(is_superuser=True).first()

        Activities.objects.create(
            user=food.user,
            textinfo=f'Your food "{food.name}" has been added into common selection.'
        )

        food.user = admin_user
        food.save()
        messages.success(request, 'Food deleted successfully.')
        return HttpResponse(status=204)
    

    return render(
        request,
        'tracker/confirm.html',
        {
            'object': food,
            'type_name': 'food',
            'option': 'Add to common:',
            'form_action': reverse('food_adopt', args=[food.pk])
        }
    )


@login_required
@user_passes_test(staff_required)
def food_delete_admin(request, pk):
    food = get_object_or_404(Food, pk=pk)

    if request.method == 'POST':

        Activities.objects.create(
            user=food.user,
            textinfo=f'A food "{food.name}" was deleted by admin.'
        )

        food.delete()
        messages.success(request, 'Food deleted successfully.')
        return HttpResponse(status=204)

    return render(
        request,
        'tracker/confirm.html',
        {
            'object': food,
            'type_name': 'food',
            'option': 'Delete',
            'form_action': reverse('food_delete_admin', args=[food.pk])
        }
    )


@login_required
@user_passes_test(staff_required)
def food_edit_admin(request, pk):
    food = get_object_or_404(Food, pk=pk)

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
