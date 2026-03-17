from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

#register
class UserRegisterTests(TestCase):
    def setUp(self):
        self.url = reverse("userregister")

    def test_register_success(self):
        response = self.client.post(self.url, {
            "username": "test",
            "email": "test@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
        })

        # jump to homepage
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        # assert user is created
        self.assertTrue(User.objects.filter(username="test").exists())
        # assert log in automaticlly
        self.assertIn("_auth_user_id", self.client.session)


    def test_register_fails_with_invalid_email(self):
        response = self.client.post(self.url, {
            "username": "test",
            "email": "not-an-email",
            "password": "StrongPass123",
            "password2": "StrongPass123",
        })

        # stay register page
        self.assertEqual(response.status_code, 200)
        # username should not exist
        self.assertFalse(User.objects.filter(username="test").exists())
        # return error
        self.assertContains(response, "Invalid email format.")


    def test_register_fails_when_username_exists(self):
        User.objects.create_user(
            username="test",
            email="old@example.com",
            password="OldPass123"
        )
        response = self.client.post(self.url, {
            "username": "test",
            "email": "new@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username already exists.")
        # only one user "test"
        self.assertEqual(User.objects.filter(username="test").count(), 1)


    def test_register_fails_when_email_exists(self):
        User.objects.create_user(
            username="olduser",
            email="test@example.com",
            password="OldPass123"
        )
        response = self.client.post(self.url, {
            "username": "test",
            "email": "test@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email already registered.")
        # only one email "test@example.com"
        self.assertFalse(User.objects.filter(username="test", email="test@example.com").exists())


    def test_register_fails_when_passwords_do_not_match(self):
        response = self.client.post(self.url, {
            "username": "test",
            "email": "test@example.com",
            "password": "StrongPass123",
            "password2": "DifferentPass123",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(User.objects.filter(username="test").exists())

#login
class UserLoginViewTests(TestCase):
    def setUp(self):
        self.login_url = reverse("userlogin")
        self.username = "test"
        self.password = "testpass123"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_login_page_get(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/login.html")

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": self.password
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        # assert login success
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.id
        )

    def test_login_fail_with_wrong_password(self):
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": "wrongpassword"
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/login.html")
        self.assertContains(response, "Invalid username or password.")

        # assert login fail: wrong password
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_fail_with_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            "username": "nouser",
            "password": "whatever"
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/login.html")
        # assert login fail: nonexistent user
        self.assertContains(response, "Invalid username or password.")
        self.assertNotIn("_auth_user_id", self.client.session)