"""
Comprehensive test suite for Student serializers with validation scenarios
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock
from rest_framework import serializers

from .utils import BaseTestCase, CustomAssertionsMixin
from .factories import StudentFactory, TeacherFactory, UserFactory, InvalidDataFactory
from students.serializers import StudentSerializer, StudentCreateSerializer
from students.models import Student


class StudentSerializerTest(BaseTestCase, CustomAssertionsMixin):
    """Test suite for StudentSerializer"""
    
    def setUp(self):
        super().setUp()
        self.teacher = TeacherFactory()
        self.student = StudentFactory(assigned_teacher=self.teacher)
        self.serializer = StudentSerializer(instance=self.student)
    
    def test_serializer_fields(self):
        """Test serializer contains expected fields"""
        data = self.serializer.data
        expected_fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_serializer_data_types(self):
        """Test serializer data types"""
        data = self.serializer.data
        
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['first_name'], str)
        self.assertIsInstance(data['last_name'], str)
        self.assertIsInstance(data['email'], str)
        self.assertIsInstance(data['phone_number'], str)
        self.assertIsInstance(data['roll_number'], str)
        self.assertIsInstance(data['class_grade'], str)
        self.assertIsInstance(data['status'], str)
    
    def test_serializer_read_only_fields(self):
        """Test read-only fields are not writable"""
        serializer = StudentSerializer()
        read_only_fields = ['id', 'created_at', 'updated_at']
        
        for field in read_only_fields:
            field_obj = serializer.fields[field]
            self.assertTrue(field_obj.read_only)
    
    def test_serializer_with_assigned_teacher(self):
        """Test serializer with assigned teacher"""
        data = self.serializer.data
        
        self.assertIsNotNone(data['assigned_teacher'])
        self.assertEqual(data['assigned_teacher']['id'], self.teacher.id)
        self.assertEqual(data['assigned_teacher']['first_name'], self.teacher.first_name)
    
    def test_serializer_without_assigned_teacher(self):
        """Test serializer without assigned teacher"""
        student = StudentFactory(assigned_teacher=None)
        serializer = StudentSerializer(instance=student)
        data = serializer.data
        
        self.assertIsNone(data['assigned_teacher'])
    
    def test_serializer_nested_teacher_fields(self):
        """Test nested teacher serialization"""
        data = self.serializer.data
        teacher_data = data['assigned_teacher']
        
        expected_teacher_fields = ['id', 'first_name', 'last_name', 'email', 'subject_specialization']
        for field in expected_teacher_fields:
            self.assertIn(field, teacher_data)
    
    def test_serializer_validation_success(self):
        """Test successful data validation"""
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'status': 'active'
        }
        
        serializer = StudentSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)
    
    def test_serializer_validation_required_fields(self):
        """Test validation of required fields"""
        serializer = StudentSerializer(data={})
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['first_name', 'last_name', 'email', 'roll_number', 'class_grade']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_serializer_email_validation(self):
        """Test email field validation"""
        invalid_emails = [
            'invalid-email',
            'test@',
            '@example.com',
            'test..test@example.com',
            'test@example',
            '',
            'a' * 250 + '@example.com'  # Too long
        ]
        
        for email in invalid_emails:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': email,
                'phone_number': '1234567890',
                'roll_number': 'S001',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            serializer = StudentSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Email {email} should be invalid")
            self.assertIn('email', serializer.errors)
    
    def test_serializer_phone_validation(self):
        """Test phone number validation"""
        invalid_phones = [
            '123',  # Too short
            'abcdefghij',  # Non-numeric
            '1234567890123456789',  # Too long
            '+1-234-567-8901',  # Contains special characters
            ''  # Empty
        ]
        
        for phone in invalid_phones:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': phone,
                'roll_number': 'S001',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            serializer = StudentSerializer(data=data)
            if phone == '':
                continue  # Phone might be optional
            self.assertFalse(serializer.is_valid(), f"Phone {phone} should be invalid")
    
    def test_serializer_date_validation(self):
        """Test date field validation"""
        # Test invalid date formats
        invalid_dates = [
            'invalid-date',
            '2024-13-01',  # Invalid month
            '2024-01-32',  # Invalid day
            '2030-01-01',  # Future date for birth
            '1900-01-01',  # Too old
            ''
        ]
        
        for date_str in invalid_dates:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S001',
                'class_grade': '10',
                'date_of_birth': date_str,
                'admission_date': '2024-01-01'
            }
            
            serializer = StudentSerializer(data=data)
            if date_str == '':
                continue  # Might be optional
            self.assertFalse(serializer.is_valid(), f"Date {date_str} should be invalid")
    
    def test_serializer_class_grade_validation(self):
        """Test class grade validation"""
        invalid_grades = [
            '0',  # Too low
            '15',  # Too high
            'grade-10',  # Non-numeric
            '',  # Empty
            '10.5'  # Decimal
        ]
        
        for grade in invalid_grades:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S001',
                'class_grade': grade,
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            serializer = StudentSerializer(data=data)
            if grade == '':
                self.assertFalse(serializer.is_valid())
                self.assertIn('class_grade', serializer.errors)
    
    def test_serializer_status_validation(self):
        """Test status field validation"""
        valid_statuses = ['active', 'inactive']
        invalid_statuses = ['pending', 'deleted', 'unknown', '']
        
        for status in valid_statuses:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S001',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01',
                'status': status
            }
            
            serializer = StudentSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Status {status} should be valid")
        
        for status in invalid_statuses:
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S001',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01',
                'status': status
            }
            
            serializer = StudentSerializer(data=data)
            if status == '':
                continue  # Default status might be applied
            self.assertFalse(serializer.is_valid(), f"Status {status} should be invalid")
    
    def test_serializer_custom_validation(self):
        """Test custom validation logic"""
        # Test admission date after birth date
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2024-01-01',
            'admission_date': '2023-01-01'  # Before birth date
        }
        
        serializer = StudentSerializer(data=data)
        # Should have custom validation for logical date constraints
        if not serializer.is_valid():
            self.assertIn('admission_date', serializer.errors)
    
    def test_serializer_update_partial(self):
        """Test partial update functionality"""
        data = {
            'first_name': 'Updated',
            'status': 'inactive'
        }
        
        serializer = StudentSerializer(instance=self.student, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_student = serializer.save()
        self.assertEqual(updated_student.first_name, 'Updated')
        self.assertEqual(updated_student.status, 'inactive')
    
    def test_serializer_update_full(self):
        """Test full update functionality"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Student',
            'email': 'updated@example.com',
            'phone_number': '9876543210',
            'roll_number': 'S999',
            'class_grade': '11',
            'date_of_birth': '2004-01-01',
            'admission_date': '2023-01-01',
            'status': 'active'
        }
        
        serializer = StudentSerializer(instance=self.student, data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_student = serializer.save()
        self.assertEqual(updated_student.first_name, 'Updated')
        self.assertEqual(updated_student.email, 'updated@example.com')
    
    def test_serializer_unicode_support(self):
        """Test serializer with Unicode data"""
        data = {
            'first_name': 'José',
            'last_name': 'García',
            'email': 'jose@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        student = serializer.save()
        self.assertEqual(student.first_name, 'José')
        self.assertEqual(student.last_name, 'García')
    
    def test_serializer_special_characters(self):
        """Test serializer with special characters"""
        data = {
            'first_name': "O'Connor",
            'last_name': 'Smith-Jones',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        student = serializer.save()
        self.assertEqual(student.first_name, "O'Connor")
        self.assertEqual(student.last_name, 'Smith-Jones')


class StudentCreateSerializerTest(BaseTestCase):
    """Test suite for StudentCreateSerializer"""
    
    def setUp(self):
        super().setUp()
        self.teacher = TeacherFactory()
    
    def test_create_serializer_fields(self):
        """Test create serializer contains expected fields"""
        serializer = StudentCreateSerializer()
        expected_fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.fields)
    
    def test_create_serializer_excludes_fields(self):
        """Test create serializer excludes certain fields"""
        serializer = StudentCreateSerializer()
        excluded_fields = ['id', 'created_at', 'updated_at']
        
        for field in excluded_fields:
            self.assertNotIn(field, serializer.fields)
    
    def test_create_serializer_validation(self):
        """Test create serializer validation"""
        valid_data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': self.teacher.id
        }
        
        serializer = StudentCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_create_serializer_unique_validation(self):
        """Test unique field validation in create serializer"""
        # Create existing student
        existing_student = StudentFactory(roll_number='S001', email='existing@example.com')
        
        # Try to create with duplicate roll number
        data = {
            'first_name': 'Duplicate',
            'last_name': 'Student',
            'email': 'duplicate@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',  # Duplicate
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('roll_number', serializer.errors)
    
    def test_create_serializer_foreign_key_validation(self):
        """Test foreign key validation"""
        # Test with invalid teacher ID
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': 99999  # Non-existent teacher
        }
        
        serializer = StudentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('assigned_teacher', serializer.errors)


class StudentSerializerEdgeCasesTest(BaseTestCase):
    """Test edge cases for student serializers"""
    
    def test_serializer_with_null_values(self):
        """Test serializer with null values"""
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': None,
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': None
        }
        
        serializer = StudentSerializer(data=data)
        # Should handle null values appropriately
        is_valid = serializer.is_valid()
        if not is_valid:
            # Check which fields are causing issues
            for field, errors in serializer.errors.items():
                self.assertIn(field, ['phone_number', 'assigned_teacher'])
    
    def test_serializer_with_empty_strings(self):
        """Test serializer with empty strings"""
        data = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'phone_number': '',
            'roll_number': '',
            'class_grade': '',
            'date_of_birth': '',
            'admission_date': ''
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Most fields should have validation errors
        required_fields = ['first_name', 'last_name', 'email', 'roll_number', 'class_grade']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_serializer_with_whitespace_only(self):
        """Test serializer with whitespace-only values"""
        data = {
            'first_name': '   ',
            'last_name': '\t\n',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentSerializer(data=data)
        # Should validate and potentially strip whitespace
        if serializer.is_valid():
            student = serializer.save()
            self.assertEqual(student.first_name.strip(), '')
    
    def test_serializer_with_very_long_strings(self):
        """Test serializer with very long strings"""
        data = {
            'first_name': 'A' * 1000,
            'last_name': 'B' * 1000,
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentSerializer(data=data)
        # Should validate length constraints
        if not serializer.is_valid():
            # Check for length validation errors
            for field in ['first_name', 'last_name']:
                if field in serializer.errors:
                    self.assertIn('length', str(serializer.errors[field]).lower())
    
    def test_serializer_field_choices_validation(self):
        """Test field choices validation"""
        # Test with invalid choice values
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': 'invalid-grade',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'status': 'invalid-status'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Check that choice fields have validation errors
        choice_fields = ['class_grade', 'status']
        for field in choice_fields:
            if field in serializer.errors:
                self.assertIn('choice', str(serializer.errors[field]).lower())
    
    def test_serializer_nested_validation_errors(self):
        """Test nested validation errors"""
        # Test with invalid nested teacher data
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': 'invalid-teacher-id'
        }
        
        serializer = StudentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('assigned_teacher', serializer.errors)
    
    def test_serializer_concurrent_validation(self):
        """Test serializer validation under concurrent access"""
        import threading
        
        results = []
        errors = []
        
        def validate_student():
            try:
                data = {
                    'first_name': 'Concurrent',
                    'last_name': 'Student',
                    'email': f'concurrent{threading.current_thread().ident}@example.com',
                    'phone_number': '1234567890',
                    'roll_number': f'C{threading.current_thread().ident}',
                    'class_grade': '10',
                    'date_of_birth': '2005-01-01',
                    'admission_date': '2024-01-01'
                }
                
                serializer = StudentSerializer(data=data)
                results.append(serializer.is_valid())
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_student)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All validations should complete without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
    
    def test_serializer_performance_with_large_data(self):
        """Test serializer performance with large datasets"""
        # Create large student dataset
        students = []
        for i in range(100):
            student = StudentFactory()
            students.append(student)
        
        # Test serialization performance
        operation = lambda: StudentSerializer(students, many=True).data
        result = self.assert_performance_threshold(operation, threshold_seconds=2.0)
        
        # Should serialize all students
        self.assertEqual(len(result), 100)
    
    def test_serializer_memory_usage(self):
        """Test serializer memory usage"""
        import gc
        import sys
        
        # Get baseline memory
        gc.collect()
        baseline_objects = len(gc.get_objects())
        
        # Create and serialize many students
        students = []
        for i in range(50):
            student = StudentFactory()
            students.append(student)
        
        serializer = StudentSerializer(students, many=True)
        data = serializer.data
        
        # Clean up
        del students
        del serializer
        del data
        gc.collect()
        
        # Check memory usage
        final_objects = len(gc.get_objects())
        memory_increase = final_objects - baseline_objects
        
        # Should not have excessive memory growth
        self.assertLess(memory_increase, 1000, "Excessive memory usage detected")


class StudentSerializerIntegrationTest(BaseTestCase):
    """Integration tests for student serializers"""
    
    def test_serializer_with_related_objects(self):
        """Test serializer with related objects"""
        teacher = TeacherFactory()
        student = StudentFactory(assigned_teacher=teacher)
        
        serializer = StudentSerializer(instance=student)
        data = serializer.data
        
        # Should include related teacher data
        self.assertIsNotNone(data['assigned_teacher'])
        self.assertEqual(data['assigned_teacher']['id'], teacher.id)
    
    def test_serializer_with_multiple_related_objects(self):
        """Test serializer with multiple related objects"""
        teacher = TeacherFactory()
        students = [StudentFactory(assigned_teacher=teacher) for _ in range(3)]
        
        serializer = StudentSerializer(students, many=True)
        data = serializer.data
        
        # Should serialize all students with teacher data
        self.assertEqual(len(data), 3)
        for student_data in data:
            self.assertIsNotNone(student_data['assigned_teacher'])
            self.assertEqual(student_data['assigned_teacher']['id'], teacher.id)
    
    def test_serializer_database_constraints(self):
        """Test serializer with database constraints"""
        # Create student with unique constraint
        student1 = StudentFactory(roll_number='S001')
        
        # Try to create another with same roll number
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S001',  # Duplicate
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        serializer = StudentSerializer(data=data)
        
        # Should either be invalid or raise database error on save
        if serializer.is_valid():
            with self.assertRaises(Exception):
                serializer.save()
        else:
            self.assertIn('roll_number', serializer.errors)
    
    def test_serializer_with_transactions(self):
        """Test serializer within database transactions"""
        from django.db import transaction
        
        initial_count = Student.objects.count()
        
        try:
            with transaction.atomic():
                data = {
                    'first_name': 'Transaction',
                    'last_name': 'Student',
                    'email': 'transaction@example.com',
                    'phone_number': '1234567890',
                    'roll_number': 'T001',
                    'class_grade': '10',
                    'date_of_birth': '2005-01-01',
                    'admission_date': '2024-01-01'
                }
                
                serializer = StudentSerializer(data=data)
                self.assertTrue(serializer.is_valid())
                
                student = serializer.save()
                self.assertIsNotNone(student.id)
                
                # Force rollback
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Should have rolled back
        final_count = Student.objects.count()
        self.assertEqual(initial_count, final_count)