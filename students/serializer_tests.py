from django.test import TestCase
from django.contrib.auth.models import User
from .models import Student
from .serializers import StudentSerializer
from teachers.models import Teacher


class StudentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='student@example.com',
            password='testpass123',
            email='student@example.com'
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )
        
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='Test',
            last_name='Teacher',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Math'
        )

    def test_student_serializer_valid_data(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_student_serializer_invalid_email(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_student_serializer_invalid_phone(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone_number': '123',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

    def test_student_serializer_short_first_name(self):
        data = {
            'first_name': 'J',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_student_serializer_short_last_name(self):
        data = {
            'first_name': 'John',
            'last_name': 'D',
            'email': 'john@example.com',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_student_serializer_short_roll_number(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone_number': '9876543210',
            'roll_number': 'ST',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('roll_number', serializer.errors)

    def test_student_serializer_duplicate_email(self):
        Student.objects.create(
            user=self.user,
            first_name='Existing',
            last_name='Student',
            email='existing@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'existing@example.com',
            'phone_number': '9876543211',
            'roll_number': 'STU002',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_student_serializer_duplicate_roll_number(self):
        Student.objects.create(
            user=self.user,
            first_name='Existing',
            last_name='Student',
            email='existing@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone_number': '9876543211',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('roll_number', serializer.errors)

    def test_student_serializer_assigned_teacher_name(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01',
            assigned_teacher=self.teacher
        )
        
        serializer = StudentSerializer(student)
        self.assertEqual(serializer.data['assigned_teacher_name'], 'Test Teacher')

    def test_student_serializer_no_assigned_teacher(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        serializer = StudentSerializer(student)
        self.assertIsNone(serializer.data['assigned_teacher_name'])