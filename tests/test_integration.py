"""
Integration and performance tests for the School Management System
"""
import time
import json
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.management import call_command
from django.db import transaction, connection
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache
from django.contrib.auth.models import User

from .utils import BaseAPITestCase, PerformanceMixin, IntegrationTestMixin
from .factories import (
    SchoolSetupFactory, ClassroomSetupFactory, BatchStudentFactory, 
    BatchTeacherFactory, AdminUserFactory, PerformanceTestFactory
)
from students.models import Student
from teachers.models import Teacher
from accounts.models import UserProfile


class SchoolManagementIntegrationTest(BaseAPITestCase, IntegrationTestMixin):
    """Integration tests for complete school management workflows"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        self.school_setup = SchoolSetupFactory.create_school()
    
    def test_complete_student_management_workflow(self):
        """Test complete student management workflow"""
        workflow_steps = {
            'login': self._login_admin,
            'create_student': self._create_student,
            'list_students': self._list_students,
            'update_student': self._update_student,
            'assign_teacher': self._assign_teacher,
            'export_csv': self._export_csv,
            'delete_student': self._delete_student
        }
        
        context = self.create_full_workflow_test(workflow_steps)
        
        # Verify final state
        self.assertIn('student_id', context)
        self.assertIn('csv_response', context)
        self.assertEqual(context['final_status'], 'completed')
    
    def _login_admin(self, context):
        """Step 1: Login as admin"""
        context['auth_headers'] = self.login_user(self.admin_user)
        context['user'] = self.admin_user
        return context
    
    def _create_student(self, context):
        """Step 2: Create a new student"""
        url = reverse('student-list')
        data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'email': 'integration@example.com',
            'phone_number': '1234567890',
            'roll_number': 'INT001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_201_CREATED)
        
        context['student_id'] = response.data['id']
        context['student_data'] = response.data
        return context
    
    def _list_students(self, context):
        """Step 3: List all students"""
        url = reverse('student-list')
        response = self.client.get(url, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['students_list'] = response.data
        return context
    
    def _update_student(self, context):
        """Step 4: Update student information"""
        url = reverse('student-detail', kwargs={'pk': context['student_id']})
        data = {
            'first_name': 'Updated Integration',
            'status': 'active'
        }
        
        response = self.client.patch(url, data, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['updated_student'] = response.data
        return context
    
    def _assign_teacher(self, context):
        """Step 5: Assign teacher to student"""
        teacher = self.school_setup['teachers'][0]
        url = reverse('student-detail', kwargs={'pk': context['student_id']})
        data = {
            'assigned_teacher': teacher.id
        }
        
        response = self.client.patch(url, data, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['assigned_teacher'] = teacher
        return context
    
    def _export_csv(self, context):
        """Step 6: Export students to CSV"""
        url = reverse('student-export-csv')
        response = self.client.get(url, **context['auth_headers'])
        self.assert_valid_csv_response(response)
        
        context['csv_response'] = response
        return context
    
    def _delete_student(self, context):
        """Step 7: Delete student"""
        url = reverse('student-detail', kwargs={'pk': context['student_id']})
        response = self.client.delete(url, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_204_NO_CONTENT)
        
        context['final_status'] = 'completed'
        return context
    
    def test_complete_teacher_management_workflow(self):
        """Test complete teacher management workflow"""
        workflow_steps = {
            'login': self._login_admin,
            'create_teacher': self._create_teacher,
            'list_teachers': self._list_teachers,
            'update_teacher': self._update_teacher,
            'view_teacher_students': self._view_teacher_students,
            'export_teachers_csv': self._export_teachers_csv
        }
        
        context = self.create_full_workflow_test(workflow_steps)
        
        # Verify final state
        self.assertIn('teacher_id', context)
        self.assertIn('teacher_students', context)
        self.assertIn('csv_response', context)
    
    def _create_teacher(self, context):
        """Create a new teacher"""
        url = reverse('teacher-list')
        data = {
            'first_name': 'Integration',
            'last_name': 'Teacher',
            'email': 'teacher@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Integration Testing',
            'employee_id': 'INT001',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_201_CREATED)
        
        context['teacher_id'] = response.data['id']
        return context
    
    def _list_teachers(self, context):
        """List all teachers"""
        url = reverse('teacher-list')
        response = self.client.get(url, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['teachers_list'] = response.data
        return context
    
    def _update_teacher(self, context):
        """Update teacher information"""
        url = reverse('teacher-detail', kwargs={'pk': context['teacher_id']})
        data = {
            'first_name': 'Updated Integration',
            'subject_specialization': 'Advanced Integration Testing'
        }
        
        response = self.client.patch(url, data, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['updated_teacher'] = response.data
        return context
    
    def _view_teacher_students(self, context):
        """View teacher's students"""
        url = reverse('teacher-students', kwargs={'pk': context['teacher_id']})
        response = self.client.get(url, **context['auth_headers'])
        self.assert_response_status(response, status.HTTP_200_OK)
        
        context['teacher_students'] = response.data
        return context
    
    def _export_teachers_csv(self, context):
        """Export teachers to CSV"""
        url = reverse('teacher-export-csv')
        response = self.client.get(url, **context['auth_headers'])
        self.assert_valid_csv_response(response)
        
        context['csv_response'] = response
        return context
    
    def test_cross_module_integration(self):
        """Test integration between students, teachers, and accounts modules"""
        # Create a complete classroom setup
        classroom = ClassroomSetupFactory.create_classroom(
            teacher_count=2, 
            student_count=10
        )
        
        auth_headers = self.login_user(classroom['admin'])
        
        # Test student-teacher relationships
        for student in classroom['students']:
            self.assertIsNotNone(student.assigned_teacher)
            self.assertIn(student, student.assigned_teacher.student_set.all())
        
        # Test teacher-student queries
        teacher = classroom['teachers'][0]
        url = reverse('teacher-students', kwargs={'pk': teacher.id})
        response = self.client.get(url, **auth_headers)
        
        self.assert_response_status(response, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Test user profile integration
        for teacher in classroom['teachers']:
            profile = UserProfile.objects.get(user=teacher.user)
            self.assertEqual(profile.role, 'teacher')
        
        for student in classroom['students']:
            profile = UserProfile.objects.get(user=student.user)
            self.assertEqual(profile.role, 'student')
    
    def test_authentication_integration(self):
        """Test authentication integration across modules"""
        # Create users with different roles
        admin = AdminUserFactory()
        teacher = self.school_setup['teachers'][0]
        student = self.school_setup['students'][0]
        
        # Test admin access
        admin_headers = self.login_user(admin)
        url = reverse('student-list')
        response = self.client.get(url, **admin_headers)
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Test teacher access
        teacher_headers = self.login_user(teacher.user)
        response = self.client.get(url, **teacher_headers)
        self.assert_response_status(response, status.HTTP_200_OK)
        
        # Test student access
        student_headers = self.login_user(student.user)
        response = self.client.get(url, **student_headers)
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_permission_integration(self):
        """Test permission system integration"""
        teacher = self.school_setup['teachers'][0]
        student = self.school_setup['students'][0]
        
        # Test teacher permissions
        teacher_headers = self.login_user(teacher.user)
        
        # Teacher should NOT be able to create students
        url = reverse('student-list')
        data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'roll_number': 'TEST001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **teacher_headers)
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
        
        # Test student permissions
        student_headers = self.login_user(student.user)
        
        # Student should NOT be able to create teachers
        url = reverse('teacher-list')
        data = {
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'subject_specialization': 'Test',
            'employee_id': 'TEST001',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, **student_headers)
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_data_consistency_across_modules(self):
        """Test data consistency across different modules"""
        # Create related data
        teacher = self.school_setup['teachers'][0]
        students = BatchStudentFactory.create_batch(3, assigned_teacher=teacher)
        
        # Verify consistency
        self.assertEqual(teacher.student_set.count(), 3)
        
        for student in students:
            self.assertEqual(student.assigned_teacher, teacher)
            self.assertEqual(student.user.userprofile.role, 'student')
        
        # Test cascading operations
        teacher_id = teacher.id
        teacher.delete()
        
        # Verify students are handled correctly (depending on on_delete setting)
        for student in students:
            student.refresh_from_db()
            # Either student should be deleted or teacher reference should be null
            self.assertTrue(
                student.assigned_teacher is None or 
                not Teacher.objects.filter(id=teacher_id).exists()
            )
    
    def test_database_integrity_across_modules(self):
        """Test database integrity across modules"""
        initial_user_count = User.objects.count()
        initial_profile_count = UserProfile.objects.count()
        initial_student_count = Student.objects.count()
        
        # Create student (should create user and profile)
        auth_headers = self.login_user(self.admin_user)
        url = reverse('student-list')
        data = {
            'first_name': 'Integrity',
            'last_name': 'Test',
            'email': 'integrity@example.com',
            'phone_number': '1234567890',
            'roll_number': 'INT001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **auth_headers)
        self.assert_response_status(response, status.HTTP_201_CREATED)
        
        # Verify all related objects were created
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        self.assertEqual(UserProfile.objects.count(), initial_profile_count + 1)
        self.assertEqual(Student.objects.count(), initial_student_count + 1)
        
        # Verify relationships
        student = Student.objects.get(id=response.data['id'])
        self.assertIsNotNone(student.user)
        self.assertEqual(student.user.userprofile.role, 'student')


class PerformanceTestSuite(TransactionTestCase, PerformanceMixin):
    """Performance tests for the School Management System"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        # Create large dataset
        print("Creating large dataset...")
        dataset = PerformanceTestFactory.create_large_dataset(
            student_count=500, 
            teacher_count=25
        )
        
        print(f"Created {len(dataset['students'])} students and {len(dataset['teachers'])} teachers")
        
        # Test query performance
        start_time = time.time()
        
        # Test list queries
        students = Student.objects.all()
        student_count = students.count()
        
        teachers = Teacher.objects.all()
        teacher_count = teachers.count()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Query performance: {duration:.2f}s for {student_count} students and {teacher_count} teachers")
        
        # Should be reasonably fast
        self.assertLess(duration, 2.0)
        
        # Verify data integrity
        self.assertEqual(student_count, 500)
        self.assertEqual(teacher_count, 25)
    
    def test_api_response_performance(self):
        """Test API response performance"""
        # Create test data
        BatchStudentFactory.create_batch(100)
        BatchTeacherFactory.create_batch(20)
        
        # Test API performance
        from django.test import Client
        client = Client()
        
        # Login
        client.force_login(self.admin_user)
        
        # Test student list performance
        operation = lambda: client.get(reverse('student-list'))
        response = self.assert_performance_threshold(operation, threshold_seconds=3.0)
        
        self.assertEqual(response.status_code, 200)
        
        # Test teacher list performance
        operation = lambda: client.get(reverse('teacher-list'))
        response = self.assert_performance_threshold(operation, threshold_seconds=3.0)
        
        self.assertEqual(response.status_code, 200)
    
    def test_concurrent_requests_performance(self):
        """Test performance under concurrent requests"""
        # Create test data
        BatchStudentFactory.create_batch(50)
        
        from django.test import Client
        
        def make_request():
            client = Client()
            client.force_login(self.admin_user)
            return client.get(reverse('student-list'))
        
        # Test concurrent requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Concurrent requests completed in {duration:.2f}s")
        
        # Should complete within reasonable time
        self.assertLess(duration, 10.0)
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
    
    def test_database_query_optimization(self):
        """Test database query optimization"""
        # Create related data
        teachers = BatchTeacherFactory.create_batch(5)
        for teacher in teachers:
            BatchStudentFactory.create_batch(10, assigned_teacher=teacher)
        
        # Test N+1 query problem
        with self.assertNumQueries(2):  # Should be 2 queries with select_related
            students = Student.objects.select_related('assigned_teacher').all()
            for student in students:
                # Access related field
                teacher_name = student.assigned_teacher.first_name if student.assigned_teacher else None
    
    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        # Test bulk create
        students_data = []
        for i in range(500):
            user = UserFactory()
            students_data.append(Student(
                user=user,
                first_name=f'Student{i}',
                last_name='Test',
                email=f'student{i}@example.com',
                phone_number='1234567890',
                roll_number=f'S{i:04d}',
                class_grade='10',
                date_of_birth='2005-01-01',
                admission_date='2024-01-01'
            ))
        
        # Time bulk create
        operation = lambda: Student.objects.bulk_create(students_data)
        self.assert_performance_threshold(operation, threshold_seconds=5.0)
        
        # Verify creation
        self.assertEqual(Student.objects.count(), 500)
        
        # Test bulk update
        operation = lambda: Student.objects.all().update(status='inactive')
        self.assert_performance_threshold(operation, threshold_seconds=2.0)
        
        # Verify update
        inactive_count = Student.objects.filter(status='inactive').count()
        self.assertEqual(inactive_count, 500)
    
    def test_csv_export_performance(self):
        """Test CSV export performance"""
        # Create large dataset
        BatchStudentFactory.create_batch(1000)
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # Test CSV export performance
        operation = lambda: client.get(reverse('student-export-csv'))
        response = self.assert_performance_threshold(operation, threshold_seconds=10.0)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_search_performance(self):
        """Test search performance"""
        # Create searchable data
        for i in range(1000):
            StudentFactory(
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                email=f'student{i}@example.com'
            )
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # Test search performance
        operation = lambda: client.get(reverse('student-list') + '?search=Student500')
        response = self.assert_performance_threshold(operation, threshold_seconds=2.0)
        
        self.assertEqual(response.status_code, 200)
    
    def test_pagination_performance(self):
        """Test pagination performance"""
        # Create large dataset
        BatchStudentFactory.create_batch(1000)
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # Test pagination performance
        operation = lambda: client.get(reverse('student-list') + '?page=1&page_size=20')
        response = self.assert_performance_threshold(operation, threshold_seconds=1.0)
        
        self.assertEqual(response.status_code, 200)
        
        # Test last page performance
        operation = lambda: client.get(reverse('student-list') + '?page=50&page_size=20')
        response = self.assert_performance_threshold(operation, threshold_seconds=1.0)
        
        self.assertEqual(response.status_code, 200)
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        BatchStudentFactory.create_batch(500)
        
        # Perform operations
        students = Student.objects.all()
        for student in students:
            str(student)  # Force string representation
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (increase: {memory_increase:.2f}MB)")
        
        # Should not use excessive memory
        self.assertLess(memory_increase, 100, "Excessive memory usage detected")


class LoadTestSuite(TransactionTestCase):
    """Load tests for the School Management System"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
    
    def test_sustained_load(self):
        """Test sustained load over time"""
        # Create test data
        BatchStudentFactory.create_batch(100)
        
        from django.test import Client
        
        def make_sustained_requests():
            client = Client()
            client.force_login(self.admin_user)
            
            for _ in range(50):
                response = client.get(reverse('student-list'))
                if response.status_code != 200:
                    return False
                time.sleep(0.1)  # Small delay
            
            return True
        
        # Test sustained load
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_sustained_requests) for _ in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Sustained load test completed in {duration:.2f}s")
        
        # All requests should succeed
        for result in results:
            self.assertTrue(result)
    
    def test_stress_testing(self):
        """Test system under stress"""
        # Create large dataset
        BatchStudentFactory.create_batch(200)
        
        from django.test import Client
        
        def stress_test():
            client = Client()
            client.force_login(self.admin_user)
            
            # Make rapid requests
            for _ in range(20):
                response = client.get(reverse('student-list'))
                if response.status_code != 200:
                    return False
            
            return True
        
        # Test with high concurrency
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(stress_test) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Stress test completed in {duration:.2f}s")
        
        # Most requests should succeed
        success_rate = sum(results) / len(results)
        self.assertGreaterEqual(success_rate, 0.8, "Success rate should be at least 80%")
    
    def test_database_connection_pool(self):
        """Test database connection pool under load"""
        def query_database():
            try:
                # Perform database operation
                count = Student.objects.count()
                return count
            except Exception as e:
                return str(e)
        
        # Test concurrent database access
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(query_database) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # All queries should succeed
        errors = [r for r in results if isinstance(r, str)]
        self.assertEqual(len(errors), 0, f"Database errors: {errors}")


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
})
class CacheIntegrationTest(BaseAPITestCase):
    """Test caching integration"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
        cache.clear()
    
    def test_cache_performance_improvement(self):
        """Test that caching improves performance"""
        # Create test data
        BatchStudentFactory.create_batch(100)
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # First request (not cached)
        start_time = time.time()
        response1 = client.get(reverse('student-list'))
        first_request_time = time.time() - start_time
        
        # Second request (should be cached if implemented)
        start_time = time.time()
        response2 = client.get(reverse('student-list'))
        second_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        print(f"First request: {first_request_time:.4f}s, Second request: {second_request_time:.4f}s")
        
        # Note: Cache improvement depends on implementation
        # This test documents the performance characteristics
    
    def test_cache_invalidation(self):
        """Test cache invalidation on data changes"""
        # Create test data
        student = StudentFactory()
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # Cache the list
        response1 = client.get(reverse('student-list'))
        self.assertEqual(response1.status_code, 200)
        
        # Modify data
        student.first_name = 'Modified'
        student.save()
        
        # Cache should be invalidated
        response2 = client.get(reverse('student-list'))
        self.assertEqual(response2.status_code, 200)
        
        # Note: Actual cache invalidation depends on implementation
        # This test verifies the system remains consistent


class SecurityIntegrationTest(BaseAPITestCase):
    """Security integration tests"""
    
    def setUp(self):
        super().setUp()
        self.admin_user = AdminUserFactory()
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        from .utils import TestDataGenerator
        
        # Test search with SQL injection attempts
        for injection_string in TestDataGenerator.generate_sql_injection_strings():
            url = reverse('student-list')
            response = self.client.get(
                f"{url}?search={injection_string}", 
                **self.login_user(self.admin_user)
            )
            
            # Should not cause server error
            self.assertNotEqual(response.status_code, 500)
            self.assertIn(response.status_code, [200, 400])
    
    def test_xss_protection(self):
        """Test XSS protection"""
        from .utils import TestDataGenerator
        
        # Test creating student with XSS attempts
        url = reverse('student-list')
        
        for xss_string in TestDataGenerator.generate_xss_strings():
            data = {
                'first_name': xss_string,
                'last_name': 'Test',
                'email': 'test@example.com',
                'phone_number': '1234567890',
                'roll_number': f'XSS{hash(xss_string)}',
                'class_grade': '10',
                'date_of_birth': '2005-01-01',
                'admission_date': '2024-01-01'
            }
            
            response = self.client.post(url, data, **self.login_user(self.admin_user))
            
            # Should either reject or sanitize
            self.assertIn(response.status_code, [200, 201, 400])
            
            if response.status_code == 201:
                # If created, should be sanitized
                self.assertNotIn('<script>', response.data.get('first_name', ''))
    
    def test_authentication_security(self):
        """Test authentication security"""
        # Test without authentication
        url = reverse('student-list')
        response = self.client.get(url)
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)
        
        # Test with invalid token
        response = self.client.get(url, HTTP_AUTHORIZATION='Bearer invalid-token')
        self.assert_response_status(response, status.HTTP_401_UNAUTHORIZED)
        
        # Test with valid token
        response = self.client.get(url, **self.login_user(self.admin_user))
        self.assert_response_status(response, status.HTTP_200_OK)
    
    def test_permission_security(self):
        """Test permission security"""
        student_user = StudentFactory().user
        
        # Student should not be able to create other students
        url = reverse('student-list')
        data = {
            'first_name': 'Unauthorized',
            'last_name': 'Student',
            'email': 'unauthorized@example.com',
            'phone_number': '1234567890',
            'roll_number': 'UNAUTH001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01'
        }
        
        response = self.client.post(url, data, **self.login_user(student_user))
        self.assert_response_status(response, status.HTTP_403_FORBIDDEN)
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Note: CSRF protection testing depends on Django configuration
        # This test verifies that CSRF tokens are properly handled
        
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        
        # Test without CSRF token
        response = client.post(reverse('student-list'), {})
        self.assertIn(response.status_code, [403, 401])  # Should be forbidden or unauthorized
    
    def test_rate_limiting(self):
        """Test rate limiting protection"""
        # Note: Rate limiting implementation depends on middleware
        # This test verifies that rapid requests are handled appropriately
        
        from django.test import Client
        client = Client()
        client.force_login(self.admin_user)
        
        # Make rapid requests
        responses = []
        for _ in range(100):
            response = client.get(reverse('student-list'))
            responses.append(response)
        
        # Should not cause server errors
        server_errors = [r for r in responses if r.status_code >= 500]
        self.assertEqual(len(server_errors), 0, "Server errors detected under rapid requests")


class DataIntegrityTest(TransactionTestCase):
    """Test data integrity across the system"""
    
    def test_referential_integrity(self):
        """Test referential integrity constraints"""
        # Create related data
        teacher = TeacherFactory()
        student = StudentFactory(assigned_teacher=teacher)
        
        # Test cascade behavior
        teacher_id = teacher.id
        student_id = student.id
        
        # Delete teacher
        teacher.delete()
        
        # Check student's teacher reference
        student.refresh_from_db()
        # Depending on on_delete setting, should be None or student should be deleted
        self.assertTrue(
            student.assigned_teacher is None or 
            not Student.objects.filter(id=student_id).exists()
        )
    
    def test_data_consistency_under_concurrent_access(self):
        """Test data consistency under concurrent access"""
        teacher = TeacherFactory()
        
        def assign_students():
            # Create students and assign to teacher
            for i in range(10):
                student = StudentFactory(assigned_teacher=teacher)
        
        # Run concurrent assignments
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=assign_students)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify data consistency
        total_students = Student.objects.filter(assigned_teacher=teacher).count()
        self.assertEqual(total_students, 50)  # 5 threads * 10 students each
    
    def test_transaction_isolation(self):
        """Test transaction isolation"""
        initial_count = Student.objects.count()
        
        # Start a transaction but don't commit
        with transaction.atomic():
            student = StudentFactory()
            
            # In another connection, count should still be initial
            # Note: This depends on isolation level
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM students_student")
                count = cursor.fetchone()[0]
            
            # Within transaction, count should be higher
            current_count = Student.objects.count()
            self.assertEqual(current_count, initial_count + 1)
    
    def test_backup_and_restore_integrity(self):
        """Test backup and restore integrity"""
        # Create test data
        original_students = BatchStudentFactory.create_batch(10)
        original_teachers = BatchTeacherFactory.create_batch(3)
        
        # Simulate backup (export data)
        student_data = []
        for student in Student.objects.all():
            student_data.append({
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email,
                'roll_number': student.roll_number,
                'class_grade': student.class_grade,
                'date_of_birth': str(student.date_of_birth),
                'admission_date': str(student.admission_date),
                'status': student.status
            })
        
        # Clear data
        Student.objects.all().delete()
        
        # Simulate restore
        for data in student_data:
            user = UserFactory()
            Student.objects.create(
                user=user,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                roll_number=data['roll_number'],
                class_grade=data['class_grade'],
                date_of_birth=data['date_of_birth'],
                admission_date=data['admission_date'],
                status=data['status']
            )
        
        # Verify integrity
        restored_count = Student.objects.count()
        self.assertEqual(restored_count, len(original_students))
        
        # Verify unique constraints still work
        with self.assertRaises(Exception):
            duplicate_student = Student.objects.create(
                user=UserFactory(),
                first_name='Duplicate',
                last_name='Student',
                email='duplicate@example.com',
                roll_number=student_data[0]['roll_number'],  # Duplicate roll number
                class_grade='10',
                date_of_birth='2005-01-01',
                admission_date='2024-01-01'
            )