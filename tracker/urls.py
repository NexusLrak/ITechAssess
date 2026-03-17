from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from . import api
from . import adminview

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', api.user_register, name='userregister'),
    path('login/', api.user_login, name='userlogin'),

    path("account/", views.account_view, name="account"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('foods/', views.food_list, name='food_list'),
    path('foods/add/', api.food_create, name='food_create'),
    path('foods/<int:pk>/edit/', api.food_edit, name='food_edit'),
    path('foods/<int:pk>/delete/', api.food_delete, name='food_delete'),

    path('records/', views.record_list, name='record_list'),
    path('records/add/', api.record_create, name='record_create'),
    path('records/<str:record_date>/', views.record_day_detail, name='record_day_detail'),
    path('records/<int:pk>/edit/', api.record_edit, name='record_edit'),
    path('records/<int:pk>/delete/', api.record_delete, name='record_delete'),

    path("analysis/", views.analysis_page, name='analysis_page'),
    path("api/analysis/", api.analysis, name='analysis'),

    path("account/profile/", api.update_profile_view, name="account_update_profile"),
    path("account/password/", api.change_password_view, name="account_change_password"),
    path("account/delete/", api.delete_account_view, name="account_delete"),

    path("management/users/", adminview.admin_user_list_view, name="admin_user_list"),
    path("management/users/<int:user_id>/", adminview.admin_user_detail_view, name="admin_user_detail"),
    path("management/users/<int:user_id>/delete/", adminview.admin_user_delete_view, name="admin_user_delete"),
]
