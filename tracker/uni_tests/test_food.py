from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from tracker.models import Food

class FoodViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.client.login(username='user1', password='testpass123')

    def valid_food_data(self):
        """
        Helper to generate valid form data that satisfies:
        calories = 4*protein + 4*carbs + 9*fat
        """
        protein = 10
        carbs = 20
        fat = 5
        calories = 4*protein + 4*carbs + 9*fat  # 40 + 80 + 45 = 165

        return {
            'name': 'Test Food',
            'unit': '100g',
            'protein': protein,
            'carbohydrates': carbs,
            'fat': fat,
            'fiber': 2,
            'calories': calories,
        }

    def invalid_food_data(self):
        """
        Data that violates calorie formula -> should trigger ValidationError
        """
        return {
            'name': 'Invalid Food',
            'unit': '100g',
            'protein': 10,
            'carbohydrates': 20,
            'fat': 5,
            'fiber': 2,
            'calories': 100,  # incorrect on purpose
        }

    def test_food_create_post_success(self):
        """POST with valid data should create food and return 204"""
        response = self.client.post(
            reverse('food_create'),
            data=self.valid_food_data()
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Food.objects.count(), 1)

    def test_food_create_invalid_calories(self):
        """POST with invalid calorie calculation should return form error"""
        response = self.client.post(
            reverse('food_create'),
            data=self.invalid_food_data()
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            None,  # non-field error (clean())
            "Calories should be165.0kcals"
        )

    def test_food_edit_post_success(self):
        """Editing with valid data should update record"""
        food = Food.objects.create(
            user=self.user,
            **self.valid_food_data()
        )

        new_data = self.valid_food_data()
        new_data['name'] = 'Updated Food'

        response = self.client.post(
            reverse('food_edit', args=[food.pk]),
            data=new_data
        )

        self.assertEqual(response.status_code, 204)
        food.refresh_from_db()
        self.assertEqual(food.name, 'Updated Food')

    def test_food_edit_invalid_calories(self):
        """Editing with invalid calories should not save"""
        food = Food.objects.create(
            user=self.user,
            **self.valid_food_data()
        )

        response = self.client.post(
            reverse('food_edit', args=[food.pk]),
            data=self.invalid_food_data()
        )

        self.assertEqual(response.status_code, 200)

        # Ensure object not modified
        food.refresh_from_db()
        self.assertEqual(food.name, 'Test Food')