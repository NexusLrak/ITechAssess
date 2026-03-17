from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tracker.models import Food, MealRecord

User = get_user_model()


class AnalysisViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

        self.food = Food.objects.create(
            user=self.user,
            name='Oats',
            unit='100g',
            calories=200.0,
            protein=10.0,
            fat=5.0,
            carbohydrates=20.0,
            fiber=8.0,
        )

        self.other_food = Food.objects.create(
            user=self.other_user,
            name='Milk',
            unit='100ml',
            calories=60.0,
            protein=3.0,
            fat=3.0,
            carbohydrates=5.0,
            fiber=0.0,
        )

        self.day1 = date(2026, 3, 16)
        self.day2 = date(2026, 3, 17)

        MealRecord.objects.create(
            user=self.user,
            meal_type='breakfast',
            quantity=2.0,
            record_date=self.day1,
            notes='',
            food_name=self.food.name,
            food_unit=self.food.unit,
            food_calories=self.food.calories,
            food_protein=self.food.protein,
            food_fat=self.food.fat,
            food_carbohydrates=self.food.carbohydrates,
            food_fiber=self.food.fiber,
        )

        MealRecord.objects.create(
            user=self.user,
            meal_type='lunch',
            quantity=1.0,
            record_date=self.day2,
            notes='',
            food_name=self.food.name,
            food_unit=self.food.unit,
            food_calories=self.food.calories,
            food_protein=self.food.protein,
            food_fat=self.food.fat,
            food_carbohydrates=self.food.carbohydrates,
            food_fiber=self.food.fiber,
        )

        MealRecord.objects.create(
            user=self.other_user,
            meal_type='dinner',
            quantity=10.0,
            record_date=self.day1,
            notes='',
            food_name=self.other_food.name,
            food_unit=self.other_food.unit,
            food_calories=self.other_food.calories,
            food_protein=self.other_food.protein,
            food_fat=self.other_food.fat,
            food_carbohydrates=self.other_food.carbohydrates,
            food_fiber=self.other_food.fiber,
        )

    def login(self):
        """Log in as the primary test user."""
        self.client.login(username='user1', password='testpass123')

    def test_analysis_page_requires_login(self):
        """Anonymous user should be redirected from analysis page."""
        response = self.client.get(reverse('analysis_page'))
        self.assertEqual(response.status_code, 302)

    def test_analysis_page_get(self):
        """GET should render the analysis page."""
        self.login()
        response = self.client.get(reverse('analysis_page'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/analysis.html')

    def test_analysis_requires_login(self):
        """Anonymous user should be redirected from analysis API."""
        response = self.client.get(reverse('analysis'))
        self.assertEqual(response.status_code, 302)

    def test_analysis_returns_weekly_json(self):
        """API should return aggregated macro calorie data for selected week."""
        self.login()
        response = self.client.get(
            reverse('analysis'),
            {'date': '2026-03-16'}
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('barData', payload)

        bar_data = payload['barData']
        self.assertEqual(len(bar_data), 6)

        lookup = {
            (row['date'], row['macro']): row
            for row in bar_data
        }

        # 2026-03-16, quantity = 2
        self.assertEqual(lookup[('2026-03-16', 'Protein')]['kcal'], 80.0)
        self.assertEqual(lookup[('2026-03-16', 'Carbs')]['kcal'], 160.0)
        self.assertEqual(lookup[('2026-03-16', 'Fat')]['kcal'], 90.0)
        self.assertEqual(lookup[('2026-03-16', 'Protein')]['dailyCalories'], 400.0)

        # 2026-03-17, quantity = 1
        self.assertEqual(lookup[('2026-03-17', 'Protein')]['kcal'], 40.0)
        self.assertEqual(lookup[('2026-03-17', 'Carbs')]['kcal'], 80.0)
        self.assertEqual(lookup[('2026-03-17', 'Fat')]['kcal'], 45.0)
        self.assertEqual(lookup[('2026-03-17', 'Protein')]['dailyCalories'], 200.0)