from django.test import TestCase
from django.contrib.auth.models import User
from .models import Teacher


class TeacherModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )

    def test_create_teacher(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        self.assertEqual(teacher.user, self.user)
        self.assertEqual(teacher.first_name, 'John')
        self.assertEqual(teacher.last_name, 'Smith')
        self.assertEqual(teacher.email, 'teacher@example.com')
        self.assertEqual(teacher.phone_number, '1234567890')
        self.assertEqual(teacher.subject, 'Mathematics')
        self.assertEqual(teacher.status, 'active')
        self.assertEqual(str(teacher), 'John Smith')

    def test_teacher_with_qualification(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics',
            qualification='M.Sc Mathematics'
        )
        
        self.assertEqual(teacher.qualification, 'M.Sc Mathematics')

    def test_teacher_with_experience(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics',
            experience_years=5
        )
        
        self.assertEqual(teacher.experience_years, 5)

    def test_teacher_with_salary(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics',
            salary=50000.00
        )
        
        self.assertEqual(float(teacher.salary), 50000.00)

    def test_teacher_default_status(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        self.assertEqual(teacher.status, 'active')

    def test_teacher_inactive_status(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics',
            status='inactive'
        )
        
        self.assertEqual(teacher.status, 'inactive')

    def test_teacher_unique_email(self):
        Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='unique@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        user2 = User.objects.create_user(
            username='teacher2@example.com',
            password='testpass123',
            email='teacher2@example.com'
        )
        
        # This should raise an error due to unique constraint
        with self.assertRaises(Exception):
            Teacher.objects.create(
                user=user2,
                first_name='Jane',
                last_name='Doe',
                email='unique@example.com',
                phone_number='1234567891',
                subject='English'
            )

    def test_teacher_default_experience(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        self.assertEqual(teacher.experience_years, 0)

    def test_teacher_null_qualification(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        self.assertIsNone(teacher.qualification)

    def test_teacher_null_salary(self):
        teacher = Teacher.objects.create(
            user=self.user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        self.assertIsNone(teacher.salary)