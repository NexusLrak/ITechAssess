from django.conf import settings
from django.db import models


class Food(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='foods')
    name = models.CharField(max_length=120)
    unit = models.CharField(max_length=30, default='100g', help_text='e.g. 100g, serving, piece')
    calories = models.FloatField()
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    carbohydrates = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name


class MealRecord(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_records')
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='records')
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES, default='breakfast')
    quantity = models.FloatField(help_text='Multiplier based on the food unit, e.g. 1 serving or 1 x 100g')
    record_date = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_date', 'meal_type', '-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.food.name} - {self.record_date}'

    @property
    def total_calories(self):
        return round(self.food.calories * self.quantity, 2)

    @property
    def total_protein(self):
        return round(self.food.protein * self.quantity, 2)

    @property
    def total_fat(self):
        return round(self.food.fat * self.quantity, 2)

    @property
    def total_carbohydrates(self):
        return round(self.food.carbohydrates * self.quantity, 2)

    @property
    def total_fiber(self):
        return round(self.food.fiber * self.quantity, 2)
