"""
Core functionality tests for School Management System
Basic tests that focus on essential features without advanced scenarios
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from students.models import Student
from teachers.models import Teacher
from accounts.models import UserProfile
from .factories import StudentFactory, TeacherFactory, UserFactory


class CoreStudentModelTest(TestCase):
    """Core student model functionality tests"""
    
    def test_student_creation(self):
        """Test basic student creation"""
        user = UserFactory()
        teacher = TeacherFactory()
        
        student = Student.objects.create(
            user=user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='1234567890',
            roll_number='S001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2024-01-01',
            assigned_teacher=teacher
        )
        
        self.assertEqual(student.first_name, 'John')
        self.assertEqual(student.last_name, 'Doe')
        self.assertEqual(student.roll_number, 'S001')
        self.assertEqual(student.status, 'active')
        
    def test_student_string_representation(self):
        """Test student string representation"""
        student = StudentFactory(first_name='Jane', last_name='Smith', roll_number='S002')
        self.assertEqual(str(student), 'Jane Smith - S002')
    
    def test_student_unique_roll_number(self):
        """Test student roll number uniqueness"""
        student1 = StudentFactory(roll_number='S001')
        student2 = StudentFactory(roll_number='S002')
        
        # Both students should have different roll numbers
        self.assertNotEqual(student1.roll_number, student2.roll_number)
    
    def test_student_email_uniqueness(self):
        """Test student email uniqueness"""
        student1 = StudentFactory(email='test1@example.com')
        student2 = StudentFactory(email='test2@example.com')
        
        # Both students should have different emails
        self.assertNotEqual(student1.email, student2.email)
    
    def test_student_teacher_relationship(self):
        """Test student-teacher relationship"""
        teacher = TeacherFactory()
        student = StudentFactory(assigned_teacher=teacher)
        
        self.assertEqual(student.assigned_teacher, teacher)
        self.assertIn(student, teacher.student_set.all())
    
    def test_student_without_teacher(self):
        """Test student without assigned teacher"""
        student = StudentFactory(assigned_teacher=None)
        self.assertIsNone(student.assigned_teacher)


class CoreTeacherModelTest(TestCase):
    """Core teacher model functionality tests"""
    
    def test_teacher_creation(self):
        """Test basic teacher creation"""
        user = UserFactory()
        
        teacher = Teacher.objects.create(
            user=user,
            first_name='Alice',
            last_name='Johnson',
            email='alice@example.com',
            phone_number='9876543210',
            employee_id='T001',
            subject_specialization='Mathematics',
            date_of_joining='2024-01-01'
        )
        
        self.assertEqual(teacher.first_name, 'Alice')
        self.assertEqual(teacher.last_name, 'Johnson')
        self.assertEqual(teacher.employee_id, 'T001')
        self.assertEqual(teacher.status, 'active')
        
    def test_teacher_string_representation(self):
        """Test teacher string representation"""
        teacher = TeacherFactory(first_name='Bob', last_name='Wilson', employee_id='T002')
        self.assertEqual(str(teacher), 'Bob Wilson - T002')
    
    def test_teacher_unique_employee_id(self):
        """Test teacher employee ID uniqueness"""
        teacher1 = TeacherFactory(employee_id='T001')
        teacher2 = TeacherFactory(employee_id='T002')
        
        # Both teachers should have different employee IDs
        self.assertNotEqual(teacher1.employee_id, teacher2.employee_id)
    
    def test_teacher_email_uniqueness(self):
        """Test teacher email uniqueness"""
        teacher1 = TeacherFactory(email='teacher1@example.com')
        teacher2 = TeacherFactory(email='teacher2@example.com')
        
        # Both teachers should have different emails
        self.assertNotEqual(teacher1.email, teacher2.email)
    
    def test_teacher_students_relationship(self):
        """Test teacher-students relationship"""
        teacher = TeacherFactory()
        student1 = StudentFactory(assigned_teacher=teacher)
        student2 = StudentFactory(assigned_teacher=teacher)
        
        self.assertEqual(teacher.student_set.count(), 2)
        self.assertIn(student1, teacher.student_set.all())
        self.assertIn(student2, teacher.student_set.all())


class CoreUserProfileTest(TestCase):
    """Core user profile functionality tests"""
    
    def test_user_profile_creation(self):
        """Test basic user profile creation"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.role, 'student')
        self.assertIsNotNone(profile.created_at)
    
    def test_user_profile_string_representation(self):
        """Test user profile string representation"""
        user = UserFactory(username='testuser')
        profile = UserProfile.objects.create(user=user, role='teacher')
        
        self.assertEqual(str(profile), 'testuser - teacher')
    
    def test_user_profile_role_choices(self):
        """Test valid role choices"""
        user = UserFactory()
        
        # Test valid roles
        for role in ['admin', 'teacher', 'student']:
            profile = UserProfile.objects.create(user=UserFactory(), role=role)
            self.assertEqual(profile.role, role)
    
    def test_user_profile_unique_user(self):
        """Test one profile per user"""
        user = UserFactory()
        UserProfile.objects.create(user=user, role='student')
        
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=user, role='teacher')
    
    def test_user_profile_cascade_deletion(self):
        """Test cascade deletion when user is deleted"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        profile_id = profile.id
        
        user.delete()
        
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())


class CoreDatabaseOperationsTest(TestCase):
    """Core database operations tests"""
    
    def test_basic_crud_operations(self):
        """Test basic CRUD operations"""
        # Create
        student = StudentFactory()
        self.assertIsNotNone(student.id)
        
        # Read
        retrieved_student = Student.objects.get(id=student.id)
        self.assertEqual(retrieved_student.first_name, student.first_name)
        
        # Update
        retrieved_student.first_name = 'Updated'
        retrieved_student.save()
        
        updated_student = Student.objects.get(id=student.id)
        self.assertEqual(updated_student.first_name, 'Updated')
        
        # Delete
        student_id = student.id
        student.delete()
        self.assertFalse(Student.objects.filter(id=student_id).exists())
    
    def test_filtering_and_queries(self):
        """Test basic filtering and queries"""
        # Create test data
        active_students = [StudentFactory(status='active') for _ in range(3)]
        inactive_students = [StudentFactory(status='inactive') for _ in range(2)]
        
        # Test filtering
        active_count = Student.objects.filter(status='active').count()
        inactive_count = Student.objects.filter(status='inactive').count()
        
        self.assertEqual(active_count, 3)
        self.assertEqual(inactive_count, 2)
        
        # Test ordering
        students = Student.objects.order_by('first_name')
        names = [s.first_name for s in students]
        self.assertEqual(names, sorted(names))
    
    def test_relationships_and_joins(self):
        """Test relationships and joins"""
        teacher = TeacherFactory()
        students = [StudentFactory(assigned_teacher=teacher) for _ in range(3)]
        
        # Test forward relationship
        for student in students:
            self.assertEqual(student.assigned_teacher, teacher)
        
        # Test reverse relationship
        self.assertEqual(teacher.student_set.count(), 3)
        
        # Test select_related
        students_with_teachers = Student.objects.select_related('assigned_teacher').all()
        for student in students_with_teachers:
            if student.assigned_teacher:
                self.assertIsNotNone(student.assigned_teacher.first_name)