"""
Comprehensive test suite for Student views with mocking and advanced patterns
"""
import json
from unittest.mock import patch, MagicMock, Mock
from django.urls import reverse
from django.test import override_settings
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from .utils import BaseAPITestCase, ConcurrencyTestMixin, CustomAssertionsMixin, timeout_test
from .factories import (
    StudentFactory, TeacherFactory, AdminUserFactory, UserFactory,
    BatchStudentFactory, InvalidDataFactory, StudentWithoutTeacherFactory
)
from students.models import Student
from students.views import StudentViewSet
from students.serializers import StudentSerializer, StudentCreateSerializer


class StudentViewSetTest(BaseAPITestCase, ConcurrencyTestMixin, CustomAssertionsMixin):
    """Comprehensive test suite for StudentViewSet"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        self.teacher = TeacherFactory()
        self.student = StudentFactory(assigned_teacher=self.teacher)
        self.viewset = StudentViewSet()
        
    def test_list_students_success(self):
        """Test successful listing of students"""
        # Create test data
        BatchStudentFactory.create_batch(5, assigned_teacher=self.teacher)
        
        url = reverse('student-list')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        
        # Verify response structure
        expected_fields = ['id', 'first_name', 'last_name', 'email', 'roll_number']
        self.assert_response_structure(response, expected_fields)
    
    def test_list_students_pagination(self):
        """Test student listing with pagination"""
        # Create large dataset
        BatchStudentFactory.create_batch(25, assigned_teacher=self.teacher)
        
        url = reverse('student-list')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assert_valid_pagination(response.data)
    
    def test_list_students_filtering(self):
        """Test student listing with filtering"""
        # Create students with different grades
        grade_10_students = BatchStudentFactory.create_grade_batch('10', 3)
        grade_11_students = BatchStudentFactory.create_grade_batch('11', 2)
        
        url = reverse('student-list')
        
        # Test filtering by grade
        response = self.client.get(f"{url}?class_grade=10", **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Test filtering by status
        response = self.client.get(f"{url}?status=active", **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_list_students_search(self):
        """Test student listing with search"""
        student = StudentFactory(first_name="John", last_name="Doe")
        
        url = reverse('student-list')
        response = self.client.get(f"{url}?search=John", **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_list_students_ordering(self):
        """Test student listing with ordering"""
        # Create students with different names
        StudentFactory(first_name="Alice")
        StudentFactory(first_name="Bob")
        StudentFactory(first_name="Charlie")
        
        url = reverse('student-list')
        response = self.client.get(f"{url}?ordering=first_name", **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        # Verify ordering
        names = [student['first_name'] for student in response.data]
        self.assertEqual(names, sorted(names))
    
    @patch('students.views.User.objects.create_user')
    @patch('accounts.models.UserProfile.objects.create')
    def test_create_student_success(self, mock_create_profile, mock_create_user):
        """Test successful student creation with mocking"""
        mock_user = Mock()
        mock_user.id = 1
        mock_create_user.return_value = mock_user
        
        url = reverse('student-list')
        data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_201_CREATED)
        mock_create_user.assert_called_once()
        mock_create_profile.assert_called_once()
    
    def test_create_student_validation_error(self):
        """Test student creation with validation errors"""
        url = reverse('student-list')
        invalid_data = InvalidDataFactory.invalid_student_data()
        
        response = self.client.post(url, invalid_data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    def test_create_student_duplicate_roll_number(self):
        """Test student creation with duplicate roll number"""
        existing_student = StudentFactory(roll_number='S001')
        
        url = reverse('student-list')
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
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    @patch('students.views.Student.objects.create')
    def test_create_student_database_error(self, mock_create):
        """Test student creation with database error"""
        mock_create.side_effect = IntegrityError("Database constraint violation")
        
        url = reverse('student-list')
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_retrieve_student_success(self):
        """Test successful student retrieval"""
        student = StudentFactory()
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], student.id)
        self.assert_valid_student(student)
    
    def test_retrieve_student_not_found(self):
        """Test student retrieval with non-existent ID"""
        url = reverse('student-detail', kwargs={'pk': 99999})
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_404_NOT_FOUND)
    
    def test_update_student_success(self):
        """Test successful student update"""
        student = StudentFactory()
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        
        # Verify database update
        student.refresh_from_db()
        self.assertEqual(student.first_name, 'Updated')
    
    @patch('django.contrib.auth.models.User.objects.filter')
    def test_update_student_with_user_data(self, mock_filter):
        """Test student update with user data modification"""
        mock_user_qs = Mock()
        mock_filter.return_value = mock_user_qs
        
        student = StudentFactory()
        url = reverse('student-detail', kwargs={'pk': student.pk})
        data = {
            'first_name': 'Updated',
            'email': 'updated@example.com'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        mock_user_qs.update.assert_called_once()
    
    def test_update_student_validation_error(self):
        """Test student update with validation error"""
        student = StudentFactory()
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        data = {
            'email': 'invalid-email-format'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_student_success(self):
        """Test successful student deletion"""
        student = StudentFactory()
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        response = self.client.delete(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assert_object_not_exists(Student, id=student.id)
    
    def test_delete_student_not_found(self):
        """Test student deletion with non-existent ID"""
        url = reverse('student-detail', kwargs={'pk': 99999})
        response = self.client.delete(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_404_NOT_FOUND)
    
    @patch('students.views.csv.writer')
    def test_export_csv_success(self, mock_writer):
        """Test successful CSV export with mocking"""
        mock_csv_writer = Mock()
        mock_writer.return_value = mock_csv_writer
        
        # Create test students
        students = BatchStudentFactory.create_batch(3)
        
        url = reverse('student-export-csv')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_valid_csv_response(response)
        
        # Verify CSV writer was called
        mock_writer.assert_called_once()
        mock_csv_writer.writerow.assert_called()
    
    def test_export_csv_empty_data(self):
        """Test CSV export with no data"""
        # Delete all students
        Student.objects.all().delete()
        
        url = reverse('student-export-csv')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_valid_csv_response(response)
    
    def test_export_csv_large_dataset(self):
        """Test CSV export with large dataset"""
        # Create large dataset
        BatchStudentFactory.create_batch(100)
        
        url = reverse('student-export-csv')
        
        # Test with performance assertion
        operation = lambda: self.client.get(url, **self.login_user(self.admin_user))
        response = self.assert_performance_threshold(operation, threshold_seconds=5.0)
        
        self.assert_valid_csv_response(response)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to student endpoints"""
        url = reverse('student-list')
        response = self.client.get(url)
        
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_denied_for_students(self):
        """Test permission denied for student users"""
        student_user = UserFactory()
        url = reverse('student-list')
        
        # Test POST request (should be forbidden for students)
        data = {'first_name': 'Test'}
        response = self.client.post(url, data, **self.login_user(student_user))
        
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_concurrent_student_creation(self):
        """Test concurrent student creation"""
        def create_student():
            url = reverse('student-list')
            data = {
                'first_name': 'Concurrent',
                'last_name': 'Student',
                'email': f'concurrent{hash(threading.current_thread())}@example.com',
                'phone_number': '1234567890',
                'roll_number': f'C{hash(threading.current_thread())}',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            return self.client.post(url, data, **self.login_user(self.admin_user))
        
        # Test with 3 concurrent requests
        results, errors = self.test_concurrent_access(create_student, num_threads=3)
        
        # Should handle concurrent creation gracefully
        self.assertEqual(len(errors), 0)
    
    @timeout_test(10)
    def test_student_list_performance(self):
        """Test student list performance with timeout"""
        # Create large dataset
        BatchStudentFactory.create_batch(500)
        
        url = reverse('student-list')
        
        # Should complete within 10 seconds
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_student_search_performance(self):
        """Test student search performance"""
        # Create students with searchable data
        for i in range(100):
            StudentFactory(first_name=f"Student{i}", last_name=f"Test{i}")
        
        url = reverse('student-list')
        
        # Test search performance
        operation = lambda: self.client.get(f"{url}?search=Student50", **self.login_user(self.admin_user))
        response = self.assert_performance_threshold(operation, threshold_seconds=2.0)
        
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error"""
        initial_count = Student.objects.count()
        
        url = reverse('student-list')
        
        # Create data that will cause a database error
        with patch('students.views.Student.objects.create') as mock_create:
            mock_create.side_effect = IntegrityError("Database error")
            
            data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S999',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            response = self.client.post(url, data, **self.login_user(self.admin_user))
            
            self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
        
        # Verify no partial data was saved
        final_count = Student.objects.count()
        self.assertEqual(initial_count, final_count)
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection in search"""
        from .utils import TestDataGenerator
        
        url = reverse('student-list')
        
        # Test with SQL injection strings
        for injection_string in TestDataGenerator.generate_sql_injection_strings():
            response = self.client.get(f"{url}?search={injection_string}", **self.login_user(self.admin_user))
            
            # Should not cause server error
            self.assertNotEqual(response.status_code, 500)
    
    def test_xss_protection(self):
        """Test XSS protection in student data"""
        from .utils import TestDataGenerator
        
        url = reverse('student-list')
        
        # Test with XSS strings
        for xss_string in TestDataGenerator.generate_xss_strings():
            data = {
                'first_name': xss_string,
                'last_name': 'Test',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S999',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            response = self.client.post(url, data, **self.login_user(self.admin_user))
            
            # Should either reject or sanitize
            if response.status_code == 201:
                # If created, should be sanitized
                self.assertNotIn('<script>', response.data['first_name'])
    
    def test_unicode_support(self):
        """Test Unicode support in student data"""
        url = reverse('student-list')
        
        data = {
            'first_name': 'José',
            'last_name': 'García',
            'email': 'jose@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'José')
    
    def test_field_validation_edge_cases(self):
        """Test field validation edge cases"""
        url = reverse('student-list')
        
        # Test with boundary values
        test_cases = [
            {'first_name': 'A' * 150},  # Very long name
            {'first_name': ''},  # Empty name
            {'phone_number': '1234567890123456789'},  # Very long phone
            {'roll_number': 'A' * 50},  # Very long roll number
            {'class_grade': '100'},  # Invalid grade
            {'date_of_birth': '2030-01-01'},  # Future date
        ]
        
        for test_data in test_cases:
            base_data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': 'S999',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            base_data.update(test_data)
            
            response = self.client.post(url, base_data, **self.login_user(self.admin_user))
            
            # Should handle validation gracefully
            self.assertIn(response.status_code, [400, 201])


class StudentViewPermissionTest(BaseAPITestCase):
    """Test permissions for student views"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        self.teacher_user = TeacherFactory().user
        self.student_user = StudentFactory().user
        self.student = StudentFactory()
    
    def test_admin_permissions(self):
        """Test admin user permissions"""
        url = reverse('student-list')
        
        # Admin should have full access
        response = self.client.get(url, **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Admin should be able to create
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_201_CREATED)
    
    def test_teacher_permissions(self):
        """Test teacher user permissions"""
        url = reverse('student-list')
        
        # Teacher should have read access
        response = self.client.get(url, **self.login_user(self.teacher_user))
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_student_permissions(self):
        """Test student user permissions"""
        url = reverse('student-list')
        
        # Student should have read access
        response = self.client.get(url, **self.login_user(self.student_user))
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_anonymous_permissions(self):
        """Test anonymous user permissions"""
        url = reverse('student-list')
        
        # Anonymous should be denied
        response = self.client.get(url)
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)


import threading