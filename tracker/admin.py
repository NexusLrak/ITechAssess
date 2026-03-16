from django.contrib import admin
from .models import Food, MealRecord


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'unit', 'calories', 'protein', 'fat', 'carbohydrates', 'fiber', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at',)


@admin.register(MealRecord)
class MealRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_name', 'meal_type', 'quantity', 'record_date', 'created_at')
    search_fields = ('user__username', 'food__name', 'notes')
    list_filter = ('meal_type', 'record_date')
