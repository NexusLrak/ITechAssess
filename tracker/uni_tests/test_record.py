from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tracker.models import Food, MealRecord

User = get_user_model()


class RecordViewTests(TestCase):
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
            name='Chicken Breast',
            unit='100g',
            calories=160.0,
            protein=30.0,
            fat=4.0,
            carbohydrates=1.0,
            fiber=0.0,
        )

        self.other_food = Food.objects.create(
            user=self.other_user,
            name='Rice',
            unit='100g',
            calories=130.0,
            protein=2.0,
            fat=1.0,
            carbohydrates=27.0,
            fiber=1.0,
        )

        self.record = MealRecord.objects.create(
            user=self.user,
            meal_type='breakfast',
            quantity=2.0,
            record_date=date(2026, 3, 16),
            notes='my breakfast',
            food_name=self.food.name,
            food_unit=self.food.unit,
            food_calories=self.food.calories,
            food_protein=self.food.protein,
            food_fat=self.food.fat,
            food_carbohydrates=self.food.carbohydrates,
            food_fiber=self.food.fiber,
        )

        self.other_record = MealRecord.objects.create(
            user=self.other_user,
            meal_type='lunch',
            quantity=1.5,
            record_date=date(2026, 3, 16),
            notes='other user meal',
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

    def valid_record_data(self):
        """Return valid POST data for MealRecordForm."""
        return {
            'food': self.food.pk,
            'meal_type': 'breakfast',
            'quantity': 1.5,
            'record_date': '2026-03-17',
            'notes': 'Test note',
        }

    def test_record_list_requires_login(self):
        """Anonymous user should be redirected to login."""
        response = self.client.get(reverse('record_list'))
        self.assertEqual(response.status_code, 302)

    def test_record_list_only_shows_current_user_data(self):
        """Record list should aggregate only current user's records."""
        self.login()
        response = self.client.get(reverse('record_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/record_list.html')

        date_list = list(response.context['date_list'])
        self.assertEqual(len(date_list), 1)

        row = date_list[0]
        self.assertEqual(row['record_date'], date(2026, 3, 16))
        self.assertEqual(row['record_count'], 1)
        self.assertAlmostEqual(row['calories'], 320.0)         # 160 * 2
        self.assertAlmostEqual(row['protein'], 60.0)           # 30 * 2
        self.assertAlmostEqual(row['fat'], 8.0)                # 4 * 2
        self.assertAlmostEqual(row['carbohydrates'], 2.0)      # 1 * 2
        self.assertAlmostEqual(row['fiber'], 0.0)

    def test_record_create_get(self):
        """GET should render the create form."""
        self.login()
        response = self.client.get(reverse('record_create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/record_form.html')
        self.assertEqual(response.context['title'], 'Add Record')

    def test_record_create_post_success(self):
        """POST valid data should create a meal record with snapshot fields."""
        self.login()
        response = self.client.post(
            reverse('record_create'),
            data=self.valid_record_data()
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(MealRecord.objects.filter(user=self.user).count(), 2)

        new_record = MealRecord.objects.filter(user=self.user).latest('pk')
        self.assertEqual(new_record.user, self.user)
        self.assertEqual(new_record.meal_type, 'breakfast')
        self.assertEqual(float(new_record.quantity), 1.5)
        self.assertEqual(new_record.record_date.isoformat(), '2026-03-17')
        self.assertEqual(new_record.notes, 'Test note')

        # Snapshot fields should be copied from selected food
        self.assertEqual(new_record.food_name, self.food.name)
        self.assertEqual(new_record.food_unit, self.food.unit)
        self.assertEqual(new_record.food_calories, self.food.calories)
        self.assertEqual(new_record.food_protein, self.food.protein)
        self.assertEqual(new_record.food_fat, self.food.fat)
        self.assertEqual(new_record.food_carbohydrates, self.food.carbohydrates)
        self.assertEqual(new_record.food_fiber, self.food.fiber)

    def test_record_create_rejects_other_users_food(self):
        """Form should reject food choices that do not belong to current user."""
        self.login()
        response = self.client.post(
            reverse('record_create'),
            data={
                'food': self.other_food.pk,
                'meal_type': 'breakfast',
                'quantity': 1.0,
                'record_date': '2026-03-17',
                'notes': 'Invalid food choice',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MealRecord.objects.filter(user=self.user).count(), 1)
        self.assertFormError(
            response.context['form'],
            'food',
            'Select a valid choice. That choice is not one of the available choices.'
        )

    def test_record_edit_get(self):
        """GET should render the edit form."""
        self.login()
        response = self.client.get(reverse('record_edit', args=[self.record.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/record_form.html')
        self.assertEqual(response.context['title'], 'Edit Record')

    def test_record_edit_post_success(self):
        """POST valid data should update record and refresh snapshot fields."""
        self.login()

        new_food = Food.objects.create(
            user=self.user,
            name='Salmon',
            unit='100g',
            calories=208.0,
            protein=20.0,
            fat=13.0,
            carbohydrates=0.0,
            fiber=0.0,
        )

        response = self.client.post(
            reverse('record_edit', args=[self.record.pk]),
            data={
                'food': new_food.pk,
                'meal_type': 'dinner',
                'quantity': 3.0,
                'record_date': '2026-03-18',
                'notes': 'Updated meal',
            }
        )

        self.assertEqual(response.status_code, 204)

        self.record.refresh_from_db()
        self.assertEqual(self.record.meal_type, 'dinner')
        self.assertEqual(float(self.record.quantity), 3.0)
        self.assertEqual(self.record.record_date.isoformat(), '2026-03-18')
        self.assertEqual(self.record.notes, 'Updated meal')

        # Snapshot fields should reflect the newly selected food
        self.assertEqual(self.record.food_name, new_food.name)
        self.assertEqual(self.record.food_unit, new_food.unit)
        self.assertEqual(self.record.food_calories, new_food.calories)
        self.assertEqual(self.record.food_protein, new_food.protein)
        self.assertEqual(self.record.food_fat, new_food.fat)
        self.assertEqual(self.record.food_carbohydrates, new_food.carbohydrates)
        self.assertEqual(self.record.food_fiber, new_food.fiber)

    def test_record_edit_cannot_access_other_users_record(self):
        """Editing another user's record should return 404."""
        self.login()
        response = self.client.get(reverse('record_edit', args=[self.other_record.pk]))
        self.assertEqual(response.status_code, 404)

    def test_record_delete_get(self):
        """GET should render delete confirmation page."""
        self.login()
        response = self.client.get(reverse('record_delete', args=[self.record.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/confirm.html')
        self.assertEqual(response.context['object'], self.record)
        self.assertEqual(response.context['type_name'], 'record')

    def test_record_delete_post_success(self):
        """POST should delete current user's record."""
        self.login()
        response = self.client.post(reverse('record_delete', args=[self.record.pk]))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(MealRecord.objects.filter(pk=self.record.pk).exists())

    def test_record_delete_cannot_delete_other_users_record(self):
        """Deleting another user's record should return 404."""
        self.login()
        response = self.client.post(reverse('record_delete', args=[self.other_record.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(MealRecord.objects.filter(pk=self.other_record.pk).exists())