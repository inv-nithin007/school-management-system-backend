from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetToken


class UserProfileModelTest(TestCase):
    def test_create_user_profile(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        profile = UserProfile.objects.create(user=user, role='student')
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.role, 'student')
        self.assertEqual(str(profile), 'testuser - student')

    def test_user_profile_default_role(self):
        user = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test2@example.com'
        )
        profile = UserProfile.objects.create(user=user)
        
        self.assertEqual(profile.role, 'student')

    def test_user_profile_admin_role(self):
        user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            email='admin@example.com'
        )
        profile = UserProfile.objects.create(user=user, role='admin')
        
        self.assertEqual(profile.role, 'admin')

    def test_user_profile_teacher_role(self):
        user = User.objects.create_user(
            username='teacher',
            password='teacherpass123',
            email='teacher@example.com'
        )
        profile = UserProfile.objects.create(user=user, role='teacher')
        
        self.assertEqual(profile.role, 'teacher')


class PasswordResetTokenModelTest(TestCase):
    def test_create_password_reset_token(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        token = PasswordResetToken.objects.create(user=user)
        
        self.assertEqual(token.user, user)
        self.assertIsNotNone(token.token)
        self.assertFalse(token.used)
        self.assertEqual(str(token), 'Reset token for testuser')

    def test_token_auto_generation(self):
        user = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test2@example.com'
        )
        token = PasswordResetToken.objects.create(user=user)
        
        self.assertTrue(len(token.token) > 0)
        self.assertTrue(len(token.token) > 50)

    def test_token_used_field(self):
        user = User.objects.create_user(
            username='testuser3',
            password='testpass123',
            email='test3@example.com'
        )
        token = PasswordResetToken.objects.create(user=user)
        
        self.assertFalse(token.used)
        
        token.used = True
        token.save()
        
        self.assertTrue(token.used)

    def test_multiple_tokens_same_user(self):
        user = User.objects.create_user(
            username='testuser4',
            password='testpass123',
            email='test4@example.com'
        )
        token1 = PasswordResetToken.objects.create(user=user)
        token2 = PasswordResetToken.objects.create(user=user)
        
        self.assertEqual(token1.user, user)
        self.assertEqual(token2.user, user)
        self.assertNotEqual(token1.token, token2.token)