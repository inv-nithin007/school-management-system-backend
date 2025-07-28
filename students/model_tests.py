from django.test import TestCase
from django.contrib.auth.models import User
from .models import Student
from teachers.models import Teacher


class StudentModelTest(TestCase):
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

    def test_create_student(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        self.assertEqual(student.user, self.user)
        self.assertEqual(student.first_name, 'John')
        self.assertEqual(student.last_name, 'Doe')
        self.assertEqual(student.email, 'student@example.com')
        self.assertEqual(student.phone_number, '9876543210')
        self.assertEqual(student.roll_number, 'STU001')
        self.assertEqual(student.class_grade, '10')
        self.assertEqual(student.status, 'active')
        self.assertEqual(str(student), 'John Doe')

    def test_student_with_teacher(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01',
            assigned_teacher=self.teacher
        )
        
        self.assertEqual(student.assigned_teacher, self.teacher)
        self.assertEqual(student.assigned_teacher.first_name, 'Test')

    def test_student_default_status(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        self.assertEqual(student.status, 'active')

    def test_student_inactive_status(self):
        student = Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01',
            status='inactive'
        )
        
        self.assertEqual(student.status, 'inactive')

    def test_student_unique_email(self):
        Student.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='unique@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        user2 = User.objects.create_user(
            username='student2@example.com',
            password='testpass123',
            email='student2@example.com'
        )
        
        # This should raise an error due to unique constraint
        with self.assertRaises(Exception):
            Student.objects.create(
                user=user2,
                first_name='Jane',
                last_name='Smith',
                email='unique@example.com',
                phone_number='9876543211',
                roll_number='STU002',
                class_grade='10',
                date_of_birth='2005-01-01',
                admission_date='2020-04-01'
            )

    def test_student_unique_roll_number(self):
        Student.objects.create(
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
        
        user2 = User.objects.create_user(
            username='student2@example.com',
            password='testpass123',
            email='student2@example.com'
        )
        
        # This should raise an error due to unique constraint
        with self.assertRaises(Exception):
            Student.objects.create(
                user=user2,
                first_name='Jane',
                last_name='Smith',
                email='jane@example.com',
                phone_number='9876543211',
                roll_number='STU001',
                class_grade='10',
                date_of_birth='2005-01-01',
                admission_date='2020-04-01'
            )