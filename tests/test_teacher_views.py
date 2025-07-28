"""
Comprehensive test suite for Teacher views with mocking and advanced patterns
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
    TeacherFactory, StudentFactory, AdminUserFactory, UserFactory,
    BatchTeacherFactory, InvalidDataFactory
)
from teachers.models import Teacher
from teachers.views import TeacherViewSet
from teachers.serializers import TeacherSerializer, TeacherCreateSerializer


class TeacherViewSetTest(BaseAPITestCase, ConcurrencyTestMixin, CustomAssertionsMixin):
    """Comprehensive test suite for TeacherViewSet"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        self.teacher = TeacherFactory()
        self.viewset = TeacherViewSet()
        
    def test_list_teachers_success(self):
        """Test successful listing of teachers"""
        # Create test data
        BatchTeacherFactory.create_batch(5)
        
        url = reverse('teacher-list')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        
        # Verify response structure
        expected_fields = ['id', 'first_name', 'last_name', 'email', 'employee_id']
        self.assert_response_structure(response, expected_fields)
    
    def test_list_teachers_pagination(self):
        """Test teacher listing with pagination"""
        # Create large dataset
        BatchTeacherFactory.create_batch(25)
        
        url = reverse('teacher-list')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assert_valid_pagination(response.data)
    
    def test_list_teachers_filtering(self):
        """Test teacher listing with filtering"""
        # Create teachers with different subjects
        math_teachers = BatchTeacherFactory.create_batch(3, subject_specialization='Mathematics')
        science_teachers = BatchTeacherFactory.create_batch(2, subject_specialization='Science')
        
        url = reverse('teacher-list')
        
        # Test filtering by subject
        response = self.client.get(f"{url}?subject_specialization=Mathematics", **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Test filtering by status
        response = self.client.get(f"{url}?status=active", **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_list_teachers_search(self):
        """Test teacher listing with search"""
        teacher = TeacherFactory(first_name="John", last_name="Doe")
        
        url = reverse('teacher-list')
        response = self.client.get(f"{url}?search=John", **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_list_teachers_ordering(self):
        """Test teacher listing with ordering"""
        # Create teachers with different names
        TeacherFactory(first_name="Alice")
        TeacherFactory(first_name="Bob")
        TeacherFactory(first_name="Charlie")
        
        url = reverse('teacher-list')
        response = self.client.get(f"{url}?ordering=first_name", **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        # Verify ordering
        names = [teacher['first_name'] for teacher in response.data]
        self.assertEqual(names, sorted(names))
    
    @patch('teachers.views.User.objects.create_user')
    @patch('accounts.models.UserProfile.objects.create')
    def test_create_teacher_success(self, mock_create_profile, mock_create_user):
        """Test successful teacher creation with mocking"""
        mock_user = Mock()
        mock_user.id = 1
        mock_create_user.return_value = mock_user
        
        url = reverse('teacher-list')
        data = {
            'first_name': 'New',
            'last_name': 'Teacher',
            'email': 'newteacher@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_201_CREATED)
        mock_create_user.assert_called_once()
        mock_create_profile.assert_called_once()
    
    def test_create_teacher_validation_error(self):
        """Test teacher creation with validation errors"""
        url = reverse('teacher-list')
        invalid_data = InvalidDataFactory.invalid_teacher_data()
        
        response = self.client.post(url, invalid_data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    def test_create_teacher_duplicate_employee_id(self):
        """Test teacher creation with duplicate employee ID"""
        existing_teacher = TeacherFactory(employee_id='T001')
        
        url = reverse('teacher-list')
        data = {
            'first_name': 'Duplicate',
            'last_name': 'Teacher',
            'email': 'duplicate@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T001',  # Duplicate
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    @patch('teachers.views.Teacher.objects.create')
    def test_create_teacher_database_error(self, mock_create):
        """Test teacher creation with database error"""
        mock_create.side_effect = IntegrityError("Database constraint violation")
        
        url = reverse('teacher-list')
        data = {
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_retrieve_teacher_success(self):
        """Test successful teacher retrieval"""
        teacher = TeacherFactory()
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], teacher.id)
        self.assert_valid_teacher(teacher)
    
    def test_retrieve_teacher_not_found(self):
        """Test teacher retrieval with non-existent ID"""
        url = reverse('teacher-detail', kwargs={'pk': 99999})
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_404_NOT_FOUND)
    
    def test_update_teacher_success(self):
        """Test successful teacher update"""
        teacher = TeacherFactory()
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        data = {
            'first_name': 'Updated',
            'subject_specialization': 'Advanced Physics'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        
        # Verify database update
        teacher.refresh_from_db()
        self.assertEqual(teacher.first_name, 'Updated')
    
    @patch('django.contrib.auth.models.User.objects.filter')
    def test_update_teacher_with_user_data(self, mock_filter):
        """Test teacher update with user data modification"""
        mock_user_qs = Mock()
        mock_filter.return_value = mock_user_qs
        
        teacher = TeacherFactory()
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        data = {
            'first_name': 'Updated',
            'email': 'updated@example.com'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        mock_user_qs.update.assert_called_once()
    
    def test_update_teacher_validation_error(self):
        """Test teacher update with validation error"""
        teacher = TeacherFactory()
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        data = {
            'email': 'invalid-email-format'
        }
        
        response = self.client.patch(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_teacher_success(self):
        """Test successful teacher deletion"""
        teacher = TeacherFactory()
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        response = self.client.delete(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assert_object_not_exists(Teacher, id=teacher.id)
    
    def test_delete_teacher_not_found(self):
        """Test teacher deletion with non-existent ID"""
        url = reverse('teacher-detail', kwargs={'pk': 99999})
        response = self.client.delete(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_404_NOT_FOUND)
    
    def test_teacher_students_endpoint(self):
        """Test teacher's students endpoint"""
        teacher = TeacherFactory()
        students = [StudentFactory(assigned_teacher=teacher) for _ in range(3)]
        
        url = reverse('teacher-students', kwargs={'pk': teacher.pk})
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify student data
        for student_data in response.data:
            self.assertIn('id', student_data)
            self.assertIn('first_name', student_data)
            self.assertIn('last_name', student_data)
    
    @patch('teachers.views.csv.writer')
    def test_export_csv_success(self, mock_writer):
        """Test successful CSV export with mocking"""
        mock_csv_writer = Mock()
        mock_writer.return_value = mock_csv_writer
        
        # Create test teachers
        teachers = BatchTeacherFactory.create_batch(3)
        
        url = reverse('teacher-export-csv')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_valid_csv_response(response)
        
        # Verify CSV writer was called
        mock_writer.assert_called_once()
        mock_csv_writer.writerow.assert_called()
    
    def test_export_csv_empty_data(self):
        """Test CSV export with no data"""
        # Delete all teachers
        Teacher.objects.all().delete()
        
        url = reverse('teacher-export-csv')
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_valid_csv_response(response)
    
    def test_export_csv_large_dataset(self):
        """Test CSV export with large dataset"""
        # Create large dataset
        BatchTeacherFactory.create_batch(100)
        
        url = reverse('teacher-export-csv')
        
        # Test with performance assertion
        operation = lambda: self.client.get(url, **self.login_user(self.admin_user))
        response = self.assert_performance_threshold(operation, threshold_seconds=5.0)
        
        self.assert_valid_csv_response(response)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to teacher endpoints"""
        url = reverse('teacher-list')
        response = self.client.get(url)
        
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_denied_for_non_admin(self):
        """Test permission denied for non-admin users"""
        teacher_user = TeacherFactory().user
        url = reverse('teacher-list')
        
        # Test POST request (should be forbidden for non-admin)
        data = {'first_name': 'Test'}
        response = self.client.post(url, data, **self.login_user(teacher_user))
        
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_concurrent_teacher_creation(self):
        """Test concurrent teacher creation"""
        def create_teacher():
            url = reverse('teacher-list')
            data = {
                'first_name': 'Concurrent',
                'last_name': 'Teacher',
                'email': f'concurrent{hash(threading.current_thread())}@example.com',
                'phone_number': '1234567890',
                'subject_specialization': 'Math',
                'employee_id': f'C{hash(threading.current_thread())}',
                'date_of_joining': '2024-01-01'
            }
            return self.client.post(url, data, **self.login_user(self.admin_user))
        
        # Test with 3 concurrent requests
        results, errors = self.test_concurrent_access(create_teacher, num_threads=3)
        
        # Should handle concurrent creation gracefully
        self.assertEqual(len(errors), 0)
    
    @timeout_test(10)
    def test_teacher_list_performance(self):
        """Test teacher list performance with timeout"""
        # Create large dataset
        BatchTeacherFactory.create_batch(300)
        
        url = reverse('teacher-list')
        
        # Should complete within 10 seconds
        response = self.client.get(url, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_teacher_search_performance(self):
        """Test teacher search performance"""
        # Create teachers with searchable data
        for i in range(100):
            TeacherFactory(first_name=f"Teacher{i}", last_name=f"Test{i}")
        
        url = reverse('teacher-list')
        
        # Test search performance
        operation = lambda: self.client.get(f"{url}?search=Teacher50", **self.login_user(self.admin_user))
        response = self.assert_performance_threshold(operation, threshold_seconds=2.0)
        
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error"""
        initial_count = Teacher.objects.count()
        
        url = reverse('teacher-list')
        
        # Create data that will cause a database error
        with patch('teachers.views.Teacher.objects.create') as mock_create:
            mock_create.side_effect = IntegrityError("Database error")
            
            data = {
                'first_name': 'Test',
                'last_name': 'Teacher',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'subject_specialization': 'Physics',
                'employee_id': 'T999',
                'date_of_joining': '2024-01-01'
            }
            
            response = self.client.post(url, data, **self.login_user(self.admin_user))
            
            self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
        
        # Verify no partial data was saved
        final_count = Teacher.objects.count()
        self.assertEqual(initial_count, final_count)
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection in search"""
        from .utils import TestDataGenerator
        
        url = reverse('teacher-list')
        
        # Test with SQL injection strings
        for injection_string in TestDataGenerator.generate_sql_injection_strings():
            response = self.client.get(f"{url}?search={injection_string}", **self.login_user(self.admin_user))
            
            # Should not cause server error
            self.assertNotEqual(response.status_code, 500)
    
    def test_xss_protection(self):
        """Test XSS protection in teacher data"""
        from .utils import TestDataGenerator
        
        url = reverse('teacher-list')
        
        # Test with XSS strings
        for xss_string in TestDataGenerator.generate_xss_strings():
            data = {
                'first_name': xss_string,
                'last_name': 'Test',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'subject_specialization': 'Physics',
                'employee_id': 'T999',
                'date_of_joining': '2024-01-01'
            }
            
            response = self.client.post(url, data, **self.login_user(self.admin_user))
            
            # Should either reject or sanitize
            if response.status_code == 201:
                # If created, should be sanitized
                self.assertNotIn('<script>', response.data['first_name'])
    
    def test_unicode_support(self):
        """Test Unicode support in teacher data"""
        url = reverse('teacher-list')
        
        data = {
            'first_name': 'José',
            'last_name': 'García',
            'email': 'jose@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Matemáticas',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        
        self.assert_response_status(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'José')
    
    def test_field_validation_edge_cases(self):
        """Test field validation edge cases"""
        url = reverse('teacher-list')
        
        # Test with boundary values
        test_cases = [
            {'first_name': 'A' * 150},  # Very long name
            {'first_name': ''},  # Empty name
            {'phone_number': '1234567890123456789'},  # Very long phone
            {'employee_id': 'A' * 50},  # Very long employee ID
            {'subject_specialization': 'A' * 200},  # Very long subject
            {'date_of_joining': '2030-01-01'},  # Future date
        ]
        
        for test_data in test_cases:
            base_data = {
                'first_name': 'Test',
                'last_name': 'Teacher',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'subject_specialization': 'Physics',
                'employee_id': 'T999',
                'date_of_joining': '2024-01-01'
            }
            base_data.update(test_data)
            
            response = self.client.post(url, base_data, **self.login_user(self.admin_user))
            
            # Should handle validation gracefully
            self.assertIn(response.status_code, [400, 201])


class TeacherViewPermissionTest(BaseAPITestCase):
    """Test permissions for teacher views"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        self.teacher_user = TeacherFactory().user
        self.student_user = StudentFactory().user
        self.teacher = TeacherFactory()
    
    def test_admin_permissions(self):
        """Test admin user permissions"""
        url = reverse('teacher-list')
        
        # Admin should have full access
        response = self.client.get(url, **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Admin should be able to create
        data = {
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        response = self.client.post(url, data, **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_201_CREATED)
    
    def test_teacher_permissions(self):
        """Test teacher user permissions"""
        url = reverse('teacher-list')
        
        # Teacher should have read-only access
        response = self.client.get(url, **self.login_user(self.teacher_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Teacher should NOT be able to create
        data = {
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        response = self.client.post(url, data, **self.login_user(self.teacher_user))
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_student_permissions(self):
        """Test student user permissions"""
        url = reverse('teacher-list')
        
        # Student should have read-only access
        response = self.client.get(url, **self.login_user(self.student_user))
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Student should NOT be able to create
        data = {
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Physics',
            'employee_id': 'T999',
            'date_of_joining': '2024-01-01'
        }
        response = self.client.post(url, data, **self.login_user(self.student_user))
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_anonymous_permissions(self):
        """Test anonymous user permissions"""
        url = reverse('teacher-list')
        
        # Anonymous should be denied
        response = self.client.get(url)
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)


import threading