from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountAndAdminViewTests(TestCase):
    def setUp(self):
        # Create a regular user for account-related tests
        self.user_password = "OldPassword123!"
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password=self.user_password,
        )

        # Create a staff user for admin-related tests
        self.staff_password = "StaffPassword123!"
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password=self.staff_password,
            is_staff=True,
        )

        # Create another normal user to be managed by admin views
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="OtherPassword123!",
        )

    def test_account_view_requires_login(self):
        # Anonymous users should be redirected to login page
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_update_profile_success(self):
        # Logged-in user should be able to update username and email
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("account_update_profile"),
            data={
                "username": "updateduser",
                "email": "updated@example.com",
            },
        )

        self.assertRedirects(response, reverse("account"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updated@example.com")

    def test_change_password_success_keeps_user_logged_in(self):
        # Password change should succeed and keep the current session valid
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("account_change_password"),
            data={
                "old_password": self.user_password,
                "new_password1": "NewSecurePassword123!",
                "new_password2": "NewSecurePassword123!",
            },
        )

        self.assertRedirects(response, reverse("account"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePassword123!"))

        # The user should still be authenticated after password change
        follow_up_response = self.client.get(reverse("account"))
        self.assertEqual(follow_up_response.status_code, 200)

    def test_delete_account_success(self):
        # User should be deleted after providing correct password and confirmation text
        self.client.force_login(self.user)
        user_id = self.user.id

        response = self.client.post(
            reverse("account_delete"),
            data={
                "password": self.user_password,
                "confirm_text": "DELETE",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_admin_user_list_requires_staff(self):
        # Non-staff users should not access the admin user list
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin_user_list"))
        self.assertEqual(response.status_code, 302)

    def test_admin_user_list_staff_can_access(self):
        # Staff users should be able to access the admin user list
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("admin_user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/adminpage.html")

    def test_admin_user_delete_cannot_delete_self(self):
        # Staff user should not be able to delete their own account from admin panel
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("admin_user_delete", kwargs={"user_id": self.staff_user.id}),
        )

        self.assertRedirects(
            response,
            reverse("admin_user_detail", kwargs={"user_id": self.staff_user.id}),
        )
        self.assertTrue(User.objects.filter(id=self.staff_user.id).exists())

    def test_admin_user_delete_success(self):
        # Staff user should be able to delete another user
        self.client.force_login(self.staff_user)
        target_id = self.other_user.id

        response = self.client.post(
            reverse("admin_user_delete", kwargs={"user_id": target_id}),
        )

        self.assertRedirects(response, reverse("admin_user_list"))
        self.assertFalse(User.objects.filter(id=target_id).exists())