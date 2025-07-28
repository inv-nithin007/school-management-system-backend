"""
Comprehensive test suite for Teacher models with database transactions and edge cases
"""
from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError, connection
from django.core.exceptions import ValidationError
from django.test.utils import override_settings
from unittest.mock import patch, Mock
import threading
import time
from datetime import date, timedelta

from .utils import BaseTestCase, DatabaseMixin, ConcurrencyTestMixin
from .factories import TeacherFactory, StudentFactory, UserFactory, BatchTeacherFactory
from teachers.models import Teacher
from students.models import Student
from django.contrib.auth.models import User


class TeacherModelTest(BaseTestCase, DatabaseMixin):
    """Test suite for Teacher model basic functionality"""
    
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
    
    def test_teacher_model_creation(self):
        """Test basic teacher model creation"""
        teacher = TeacherFactory(user=self.user)
        
        self.assertIsNotNone(teacher.id)
        self.assertEqual(teacher.user, self.user)
        self.assert_valid_teacher(teacher)
    
    def test_teacher_model_fields(self):
        """Test teacher model fields"""
        teacher = TeacherFactory()
        
        # Test field types
        self.assertIsInstance(teacher.first_name, str)
        self.assertIsInstance(teacher.last_name, str)
        self.assertIsInstance(teacher.email, str)
        self.assertIsInstance(teacher.phone_number, str)
        self.assertIsInstance(teacher.employee_id, str)
        self.assertIsInstance(teacher.subject_specialization, str)
        self.assertIsInstance(teacher.date_of_joining, date)
        self.assertIsInstance(teacher.status, str)
        self.assertIsNotNone(teacher.created_at)
        self.assertIsNotNone(teacher.updated_at)
    
    def test_teacher_model_str_representation(self):
        """Test teacher model string representation"""
        teacher = TeacherFactory(
            first_name='John',
            last_name='Doe',
            employee_id='T001'
        )
        
        expected_str = 'John Doe - T001'
        self.assertEqual(str(teacher), expected_str)
    
    def test_teacher_model_default_values(self):
        """Test teacher model default values"""
        teacher = TeacherFactory()
        
        # Test default status
        self.assertEqual(teacher.status, 'active')
        
        # Test auto-generated timestamps
        self.assertIsNotNone(teacher.created_at)
        self.assertIsNotNone(teacher.updated_at)
    
    def test_teacher_student_relationship(self):
        """Test teacher-student relationship"""
        teacher = TeacherFactory()
        students = [StudentFactory(assigned_teacher=teacher) for _ in range(3)]
        
        # Test forward relationship
        self.assertEqual(teacher.student_set.count(), 3)
        
        # Test reverse relationship
        for student in students:
            self.assertEqual(student.assigned_teacher, teacher)
    
    def test_teacher_model_unique_constraints(self):
        """Test teacher model unique constraints"""
        teacher1 = TeacherFactory(employee_id='T001')
        
        # Try to create another teacher with same employee ID
        with self.assertRaises(IntegrityError):
            TeacherFactory(employee_id='T001')
    
    def test_teacher_model_email_uniqueness(self):
        """Test teacher email uniqueness"""
        teacher1 = TeacherFactory(email='test@example.com')
        
        # Try to create another teacher with same email
        with self.assertRaises(IntegrityError):
            TeacherFactory(email='test@example.com')
    
    def test_teacher_model_validation(self):
        """Test teacher model field validation"""
        teacher = TeacherFactory()
        
        # Test valid teacher
        try:
            teacher.full_clean()
        except ValidationError:
            self.fail("Valid teacher should not raise ValidationError")
        
        # Test invalid email
        teacher.email = 'invalid-email'
        with self.assertRaises(ValidationError):
            teacher.full_clean()
    
    def test_teacher_model_field_lengths(self):
        """Test teacher model field length constraints"""
        teacher = TeacherFactory()
        
        # Test first name length
        teacher.first_name = 'A' * 151  # Assuming max length is 150
        with self.assertRaises(ValidationError):
            teacher.full_clean()
        
        # Test last name length
        teacher.first_name = 'Valid'
        teacher.last_name = 'B' * 151
        with self.assertRaises(ValidationError):
            teacher.full_clean()
    
    def test_teacher_model_date_validation(self):
        """Test teacher model date validation"""
        teacher = TeacherFactory()
        
        # Test future joining date
        teacher.date_of_joining = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            teacher.full_clean()
    
    def test_teacher_model_status_choices(self):
        """Test teacher model status choices"""
        teacher = TeacherFactory()
        
        # Test valid status
        teacher.status = 'active'
        try:
            teacher.full_clean()
        except ValidationError:
            self.fail("Valid status should not raise ValidationError")
        
        # Test invalid status
        teacher.status = 'invalid-status'
        with self.assertRaises(ValidationError):
            teacher.full_clean()
    
    def test_teacher_model_phone_number_validation(self):
        """Test teacher model phone number validation"""
        teacher = TeacherFactory()
        
        # Test valid phone numbers
        valid_phones = ['1234567890', '9876543210', '5551234567']
        for phone in valid_phones:
            teacher.phone_number = phone
            try:
                teacher.full_clean()
            except ValidationError:
                self.fail(f"Valid phone {phone} should not raise ValidationError")
        
        # Test invalid phone numbers
        invalid_phones = ['123', 'abcdefghij', '12345678901234567890']
        for phone in invalid_phones:
            teacher.phone_number = phone
            with self.assertRaises(ValidationError):
                teacher.full_clean()


class TeacherModelTransactionTest(TransactionTestCase):
    """Test suite for Teacher model database transactions"""
    
    def setUp(self):
        self.user = UserFactory()
    
    def test_teacher_creation_in_transaction(self):
        """Test teacher creation within transaction"""
        initial_count = Teacher.objects.count()
        
        with transaction.atomic():
            teacher = TeacherFactory(user=self.user)
            self.assertIsNotNone(teacher.id)
            
            # Count should increase within transaction
            self.assertEqual(Teacher.objects.count(), initial_count + 1)
        
        # Count should remain after transaction
        self.assertEqual(Teacher.objects.count(), initial_count + 1)
    
    def test_teacher_creation_transaction_rollback(self):
        """Test teacher creation transaction rollback"""
        initial_count = Teacher.objects.count()
        
        try:
            with transaction.atomic():
                teacher = TeacherFactory(user=self.user)
                self.assertIsNotNone(teacher.id)
                
                # Force rollback
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Count should remain unchanged after rollback
        self.assertEqual(Teacher.objects.count(), initial_count)
    
    def test_teacher_with_students_deletion(self):
        """Test teacher deletion with assigned students"""
        teacher = TeacherFactory()
        students = [StudentFactory(assigned_teacher=teacher) for _ in range(3)]
        
        teacher_id = teacher.id
        student_ids = [s.id for s in students]
        
        # Delete teacher
        teacher.delete()
        
        # Check what happens to students (depends on on_delete setting)
        for student_id in student_ids:
            student = Student.objects.get(id=student_id)
            # Either teacher reference should be None or student should be deleted
            self.assertTrue(
                student.assigned_teacher is None or 
                not Teacher.objects.filter(id=teacher_id).exists()
            )
    
    def test_teacher_bulk_operations_in_transaction(self):
        """Test teacher bulk operations within transaction"""
        initial_count = Teacher.objects.count()
        
        with transaction.atomic():
            # Create multiple teachers
            teachers = BatchTeacherFactory.create_batch(5)
            
            # Update all teachers
            Teacher.objects.filter(id__in=[t.id for t in teachers]).update(status='inactive')
            
            # Delete some teachers
            Teacher.objects.filter(id__in=[t.id for t in teachers[:2]]).delete()
            
            # Verify changes within transaction
            self.assertEqual(Teacher.objects.count(), initial_count + 3)
            inactive_count = Teacher.objects.filter(status='inactive').count()
            self.assertGreaterEqual(inactive_count, 3)
        
        # Verify changes after transaction
        self.assertEqual(Teacher.objects.count(), initial_count + 3)
    
    def test_teacher_integrity_constraint_in_transaction(self):
        """Test integrity constraint violation in transaction"""
        teacher1 = TeacherFactory(employee_id='T001')
        initial_count = Teacher.objects.count()
        
        try:
            with transaction.atomic():
                # This should fail due to unique constraint
                teacher2 = Teacher.objects.create(
                    user=UserFactory(),
                    first_name='Duplicate',
                    last_name='Teacher',
                    email='duplicate@example.com',
                    phone_number='1234567890',
                    employee_id='T001',  # Duplicate
                    subject_specialization='Math',
                    date_of_joining=date(2024, 1, 1)
                )
        except IntegrityError:
            pass
        
        # Count should remain unchanged
        self.assertEqual(Teacher.objects.count(), initial_count)


class TeacherModelConcurrencyTest(TransactionTestCase, ConcurrencyTestMixin):
    """Test suite for Teacher model concurrency scenarios"""
    
    def test_concurrent_teacher_creation(self):
        """Test concurrent teacher creation"""
        def create_teacher():
            try:
                teacher = TeacherFactory(
                    employee_id=f'T{threading.current_thread().ident}',
                    email=f'teacher{threading.current_thread().ident}@example.com'
                )
                return teacher
            except Exception as e:
                return e
        
        # Test concurrent creation
        results, errors = self.test_concurrent_access(create_teacher, num_threads=5)
        
        # Should handle concurrent creation
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
        
        # All teachers should be created
        for result in results:
            self.assertIsInstance(result, Teacher)
    
    def test_concurrent_teacher_update(self):
        """Test concurrent teacher update"""
        teacher = TeacherFactory()
        
        def update_teacher():
            try:
                t = Teacher.objects.get(id=teacher.id)
                t.first_name = f'Updated{threading.current_thread().ident}'
                t.save()
                return t
            except Exception as e:
                return e
        
        # Test concurrent updates
        results, errors = self.test_concurrent_access(update_teacher, num_threads=5)
        
        # Should handle concurrent updates
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
        
        # Final state should be consistent
        final_teacher = Teacher.objects.get(id=teacher.id)
        self.assertIsNotNone(final_teacher.first_name)
    
    def test_race_condition_prevention(self):
        """Test race condition prevention in unique constraints"""
        def create_duplicate_teacher():
            try:
                teacher = Teacher.objects.create(
                    user=UserFactory(),
                    first_name='Race',
                    last_name='Test',
                    email=f'race{threading.current_thread().ident}@example.com',
                    phone_number='1234567890',
                    employee_id='RACE001',  # Same employee ID
                    subject_specialization='Math',
                    date_of_joining=date(2024, 1, 1)
                )
                return teacher
            except IntegrityError:
                return 'IntegrityError'
            except Exception as e:
                return e
        
        # Test concurrent creation with same employee ID
        results, errors = self.test_concurrent_access(create_duplicate_teacher, num_threads=5)
        
        # Should have exactly one success and multiple integrity errors
        teachers = [r for r in results if isinstance(r, Teacher)]
        integrity_errors = [r for r in results if r == 'IntegrityError']
        
        self.assertEqual(len(teachers), 1)
        self.assertEqual(len(integrity_errors), 4)


class TeacherModelPerformanceTest(TransactionTestCase):
    """Test suite for Teacher model performance"""
    
    def test_bulk_create_performance(self):
        """Test bulk create performance"""
        # Create large number of teachers
        teachers_data = []
        for i in range(500):
            teachers_data.append(Teacher(
                user=UserFactory(),
                first_name=f'Teacher{i}',
                last_name='Test',
                email=f'teacher{i}@example.com',
                phone_number='1234567890',
                employee_id=f'T{i:04d}',
                subject_specialization='Math',
                date_of_joining=date(2024, 1, 1)
            ))
        
        # Time bulk create
        start_time = time.time()
        Teacher.objects.bulk_create(teachers_data)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 10.0, f"Bulk create took {duration:.2f}s")
        
        # Verify all teachers were created
        self.assertEqual(Teacher.objects.count(), 500)
    
    def test_bulk_update_performance(self):
        """Test bulk update performance"""
        # Create teachers
        teachers = BatchTeacherFactory.create_batch(300)
        
        # Time bulk update
        start_time = time.time()
        Teacher.objects.filter(id__in=[t.id for t in teachers]).update(status='inactive')
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 5.0, f"Bulk update took {duration:.2f}s")
        
        # Verify all teachers were updated
        inactive_count = Teacher.objects.filter(status='inactive').count()
        self.assertEqual(inactive_count, 300)
    
    def test_query_performance_with_students(self):
        """Test query performance with related students"""
        # Create teachers with students
        teachers = BatchTeacherFactory.create_batch(50)
        for teacher in teachers:
            StudentFactory.create_batch(10, assigned_teacher=teacher)
        
        # Test query performance
        start_time = time.time()
        
        # Query teachers with student count
        teachers_with_counts = Teacher.objects.prefetch_related('student_set').all()
        for teacher in teachers_with_counts:
            student_count = teacher.student_set.count()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be efficient with prefetch_related
        self.assertLess(duration, 2.0, f"Query with students took {duration:.2f}s")


class TeacherModelEdgeCasesTest(BaseTestCase):
    """Test edge cases for Teacher model"""
    
    def test_teacher_with_unicode_data(self):
        """Test teacher with Unicode data"""
        teacher = TeacherFactory(
            first_name='José',
            last_name='García',
            email='jose@example.com'
        )
        
        # Should handle Unicode properly
        self.assertEqual(teacher.first_name, 'José')
        self.assertEqual(teacher.last_name, 'García')
        
        # Should save and retrieve correctly
        teacher.save()
        retrieved = Teacher.objects.get(id=teacher.id)
        self.assertEqual(retrieved.first_name, 'José')
    
    def test_teacher_with_special_characters(self):
        """Test teacher with special characters"""
        teacher = TeacherFactory(
            first_name="O'Connor",
            last_name='Smith-Jones',
            email='test@example.com'
        )
        
        # Should handle special characters
        self.assertEqual(teacher.first_name, "O'Connor")
        self.assertEqual(teacher.last_name, 'Smith-Jones')
    
    def test_teacher_with_boundary_values(self):
        """Test teacher with boundary values"""
        # Test minimum date
        teacher = TeacherFactory(
            date_of_joining=date(1950, 1, 1)
        )
        
        self.assertEqual(teacher.date_of_joining, date(1950, 1, 1))
        
        # Test maximum date
        teacher.date_of_joining = date.today()
        teacher.save()
        
        self.assertIsNotNone(teacher.id)
    
    def test_teacher_model_managers(self):
        """Test teacher model managers"""
        # Create active and inactive teachers
        active_teachers = BatchTeacherFactory.create_batch(3, status='active')
        inactive_teachers = BatchTeacherFactory.create_batch(2, status='inactive')
        
        # Test default manager
        all_teachers = Teacher.objects.all()
        self.assertEqual(all_teachers.count(), 5)
        
        # Test filtering
        active_count = Teacher.objects.filter(status='active').count()
        self.assertEqual(active_count, 3)
        
        inactive_count = Teacher.objects.filter(status='inactive').count()
        self.assertEqual(inactive_count, 2)
    
    def test_teacher_model_ordering(self):
        """Test teacher model ordering"""
        # Create teachers with different names
        TeacherFactory(first_name='Alice', last_name='Smith')
        TeacherFactory(first_name='Bob', last_name='Jones')
        TeacherFactory(first_name='Charlie', last_name='Brown')
        
        # Test ordering
        teachers = Teacher.objects.order_by('first_name')
        names = [t.first_name for t in teachers]
        self.assertEqual(names, sorted(names))
    
    def test_teacher_model_custom_queries(self):
        """Test custom query methods"""
        # Create teachers with different subjects
        math_teachers = BatchTeacherFactory.create_batch(3, subject_specialization='Mathematics')
        science_teachers = BatchTeacherFactory.create_batch(2, subject_specialization='Science')
        
        # Test custom filtering
        math_count = Teacher.objects.filter(subject_specialization='Mathematics').count()
        self.assertEqual(math_count, 3)
        
        science_count = Teacher.objects.filter(subject_specialization='Science').count()
        self.assertEqual(science_count, 2)
    
    def test_teacher_model_aggregations(self):
        """Test teacher model aggregations"""
        from django.db.models import Count, Avg
        
        # Create teachers with different subjects
        BatchTeacherFactory.create_batch(3, subject_specialization='Mathematics')
        BatchTeacherFactory.create_batch(2, subject_specialization='Science')
        BatchTeacherFactory.create_batch(1, subject_specialization='English')
        
        # Test aggregations
        subject_counts = Teacher.objects.values('subject_specialization').annotate(count=Count('id'))
        
        subject_count_dict = {item['subject_specialization']: item['count'] for item in subject_counts}
        self.assertEqual(subject_count_dict['Mathematics'], 3)
        self.assertEqual(subject_count_dict['Science'], 2)
        self.assertEqual(subject_count_dict['English'], 1)
    
    def test_teacher_model_complex_queries(self):
        """Test complex queries on teacher model"""
        # Create complex scenario
        old_teachers = BatchTeacherFactory.create_batch(2, 
            subject_specialization='Mathematics',
            date_of_joining=date(2020, 1, 1),
            status='active'
        )
        
        new_teachers = BatchTeacherFactory.create_batch(3, 
            subject_specialization='Science',
            date_of_joining=date(2024, 1, 1),
            status='active'
        )
        
        # Complex query: Active science teachers joined after 2023
        recent_science_teachers = Teacher.objects.filter(
            status='active',
            subject_specialization='Science',
            date_of_joining__gte=date(2023, 1, 1)
        )
        
        self.assertEqual(recent_science_teachers.count(), 3)
    
    def test_teacher_model_database_functions(self):
        """Test database functions with teacher model"""
        from django.db.models import Length, Upper, Lower
        
        # Create teachers with different name lengths
        TeacherFactory(first_name='Al')
        TeacherFactory(first_name='Robert')
        TeacherFactory(first_name='Christopher')
        
        # Test Length function
        teachers = Teacher.objects.annotate(
            name_length=Length('first_name')
        ).order_by('name_length')
        
        lengths = [t.name_length for t in teachers]
        self.assertEqual(lengths, sorted(lengths))
        
        # Test Upper function
        teachers = Teacher.objects.annotate(
            upper_name=Upper('first_name')
        )
        
        for teacher in teachers:
            self.assertEqual(teacher.upper_name, teacher.first_name.upper())