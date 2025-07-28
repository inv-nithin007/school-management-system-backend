from django.test import TestCase
from django.contrib.auth.models import User
from .models import Teacher
from .serializers import TeacherSerializer


class TeacherSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )

    def test_teacher_serializer_valid_data(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics',
            'qualification': 'M.Sc Mathematics',
            'experience_years': 5,
            'salary': 50000.00
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_teacher_serializer_invalid_email(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'invalid-email',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_teacher_serializer_invalid_phone(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '123',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

    def test_teacher_serializer_short_first_name(self):
        data = {
            'first_name': 'J',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_teacher_serializer_short_last_name(self):
        data = {
            'first_name': 'John',
            'last_name': 'S',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_teacher_serializer_short_subject(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'M'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('subject', serializer.errors)

    def test_teacher_serializer_duplicate_email(self):
        Teacher.objects.create(
            user=self.user,
            first_name='Existing',
            last_name='Teacher',
            email='existing@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'existing@example.com',
            'phone_number': '1234567891',
            'subject': 'English'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_teacher_serializer_first_name_with_numbers(self):
        data = {
            'first_name': 'John123',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_teacher_serializer_last_name_with_numbers(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith123',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_teacher_serializer_valid_with_spaces_in_name(self):
        data = {
            'first_name': 'John Paul',
            'last_name': 'Smith Jones',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_teacher_serializer_minimal_data(self):
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        
        serializer = TeacherSerializer(data=data)
        self.assertTrue(serializer.is_valid())