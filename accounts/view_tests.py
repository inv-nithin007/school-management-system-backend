from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile, PasswordResetToken


class LoginViewTest(APITestCase):
    def test_login_success(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        UserProfile.objects.create(user=user, role='student')
        
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username(self):
        url = reverse('login')
        data = {
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        url = reverse('login')
        data = {
            'username': 'testuser'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterViewTest(APITestCase):
    def test_register_success(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_existing_username(self):
        User.objects.create_user(
            username='existinguser',
            password='pass123',
            email='existing@example.com'
        )
        
        url = reverse('register')
        data = {
            'username': 'existinguser',
            'password': 'newpass123',
            'email': 'new@example.com'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ForgotPasswordViewTest(APITestCase):
    def test_forgot_password_success(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        url = reverse('forgot_password')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordResetToken.objects.filter(user=user).exists())

    def test_forgot_password_invalid_email(self):
        url = reverse('forgot_password')
        data = {'email': 'invalid@example.com'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_forgot_password_missing_email(self):
        url = reverse('forgot_password')
        data = {}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResetPasswordViewTest(APITestCase):
    def test_reset_password_success(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        token = PasswordResetToken.objects.create(user=user)
        
        url = reverse('reset_password')
        data = {
            'token': token.token,
            'new_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpassword123'))

    def test_reset_password_invalid_token(self):
        url = reverse('reset_password')
        data = {
            'token': 'invalidtoken',
            'new_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_short_password(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        token = PasswordResetToken.objects.create(user=user)
        
        url = reverse('reset_password')
        data = {
            'token': token.token,
            'new_password': '123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ChangePasswordViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='oldpass123',
            email='test@example.com'
        )
        UserProfile.objects.create(user=self.user, role='student')

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('change_password')
        data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass456'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))

    def test_change_password_wrong_current_password(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('change_password')
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass456'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_missing_fields(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('change_password')
        data = {
            'current_password': 'oldpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_short_new_password(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('change_password')
        data = {
            'current_password': 'oldpass123',
            'new_password': '123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_same_as_current(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('change_password')
        data = {
            'current_password': 'oldpass123',
            'new_password': 'oldpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        url = reverse('change_password')
        data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass456'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
