"""
Test utilities and helper functions for consistent testing
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test.utils import override_settings
import tempfile
import os
from datetime import datetime, timedelta


class TestDataMixin:
    """Mixin providing common test data and utilities"""
    
    @classmethod
    def create_test_csv_file(cls, data, filename='test.csv'):
        """Create a temporary CSV file for testing"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        if data:
            # Write header
            writer.writerow(data[0].keys())
            # Write data rows
            for row in data:
                writer.writerow(row.values())
        
        content = output.getvalue()
        return SimpleUploadedFile(filename, content.encode('utf-8'), content_type='text/csv')
    
    @classmethod
    def create_test_image_file(cls, filename='test.jpg'):
        """Create a temporary image file for testing"""
        from PIL import Image
        from io import BytesIO
        
        image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
        
        return SimpleUploadedFile(filename, buffer.read(), content_type='image/jpeg')
    
    @staticmethod
    def assert_response_contains_fields(response, fields):
        """Assert that response contains specified fields"""
        for field in fields:
            assert field in response.data, f"Field '{field}' not found in response"
    
    @staticmethod
    def assert_response_excludes_fields(response, fields):
        """Assert that response excludes specified fields"""
        for field in fields:
            assert field not in response.data, f"Field '{field}' should not be in response"
    
    @staticmethod
    def assert_pagination_response(response, expected_count=None):
        """Assert that response is properly paginated"""
        assert 'count' in response.data, "Pagination 'count' field missing"
        assert 'next' in response.data, "Pagination 'next' field missing"
        assert 'previous' in response.data, "Pagination 'previous' field missing"
        assert 'results' in response.data, "Pagination 'results' field missing"
        
        if expected_count:
            assert response.data['count'] == expected_count, f"Expected {expected_count} items, got {response.data['count']}"


class AuthenticationMixin:
    """Mixin providing authentication utilities"""
    
    def get_auth_header(self, user):
        """Get JWT authentication header for user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def login_user(self, user):
        """Login user and return auth headers"""
        return self.get_auth_header(user)
    
    def assert_authentication_required(self, url, method='GET'):
        """Assert that endpoint requires authentication"""
        response = getattr(self.client, method.lower())(url)
        self.assertEqual(response.status_code, 401)
    
    def assert_permission_denied(self, url, user, method='GET', data=None):
        """Assert that user has no permission for endpoint"""
        headers = self.get_auth_header(user)
        response = getattr(self.client, method.lower())(url, data, **headers)
        self.assertEqual(response.status_code, 403)


class MockingMixin:
    """Mixin providing mocking utilities"""
    
    def mock_email_backend(self):
        """Mock email backend for testing"""
        return patch('django.core.mail.backends.smtp.EmailBackend.send_messages')
    
    def mock_file_storage(self):
        """Mock file storage for testing"""
        return patch('django.core.files.storage.default_storage.save')
    
    def mock_external_api(self, api_url, response_data=None, status_code=200):
        """Mock external API calls"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data or {}
        
        return patch('requests.get', return_value=mock_response)
    
    def mock_database_error(self, exception_type=Exception):
        """Mock database errors for testing"""
        return patch('django.db.models.Model.save', side_effect=exception_type("Database error"))


class PerformanceMixin:
    """Mixin providing performance testing utilities"""
    
    def time_operation(self, operation, *args, **kwargs):
        """Time an operation and return duration"""
        import time
        start_time = time.time()
        result = operation(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        return result, duration
    
    def assert_query_count(self, expected_count):
        """Assert that a specific number of queries are executed"""
        from django.test.utils import override_settings
        from django.db import connection
        
        return self.assertNumQueries(expected_count)
    
    def assert_performance_threshold(self, operation, threshold_seconds=1.0, *args, **kwargs):
        """Assert that operation completes within threshold"""
        result, duration = self.time_operation(operation, *args, **kwargs)
        self.assertLessEqual(duration, threshold_seconds, 
                           f"Operation took {duration:.2f}s, exceeding threshold of {threshold_seconds}s")
        return result


class DatabaseMixin:
    """Mixin providing database testing utilities"""
    
    def assert_object_exists(self, model, **kwargs):
        """Assert that object exists in database"""
        self.assertTrue(model.objects.filter(**kwargs).exists())
    
    def assert_object_not_exists(self, model, **kwargs):
        """Assert that object does not exist in database"""
        self.assertFalse(model.objects.filter(**kwargs).exists())
    
    def assert_object_count(self, model, expected_count, **kwargs):
        """Assert object count in database"""
        actual_count = model.objects.filter(**kwargs).count()
        self.assertEqual(actual_count, expected_count)
    
    def test_transaction_rollback(self, operation):
        """Test that operation rolls back on error"""
        from django.db import transaction
        
        initial_count = User.objects.count()
        
        try:
            with transaction.atomic():
                operation()
                raise Exception("Force rollback")
        except Exception:
            pass
        
        final_count = User.objects.count()
        self.assertEqual(initial_count, final_count)


class BaseTestCase(TestCase, TestDataMixin, AuthenticationMixin, MockingMixin, 
                  PerformanceMixin, DatabaseMixin):
    """Base test case with all utilities"""
    
    def setUp(self):
        """Set up test case"""
        super().setUp()
        self.maxDiff = None  # Show full diff on assertion failures
    
    def tearDown(self):
        """Clean up after test"""
        super().tearDown()
        # Clean up any temporary files
        self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during tests"""
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith('test_') and filename.endswith('.csv'):
                try:
                    os.remove(os.path.join(temp_dir, filename))
                except OSError:
                    pass


class BaseAPITestCase(APITestCase, TestDataMixin, AuthenticationMixin, MockingMixin, 
                     PerformanceMixin, DatabaseMixin):
    """Base API test case with all utilities"""
    
    def setUp(self):
        """Set up API test case"""
        super().setUp()
        self.maxDiff = None
    
    def tearDown(self):
        """Clean up after API test"""
        super().tearDown()
        self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during tests"""
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith('test_') and filename.endswith('.csv'):
                try:
                    os.remove(os.path.join(temp_dir, filename))
                except OSError:
                    pass
    
    def assert_response_status(self, response, expected_status):
        """Assert response status with detailed error info"""
        if response.status_code != expected_status:
            error_msg = f"Expected status {expected_status}, got {response.status_code}"
            if hasattr(response, 'data'):
                error_msg += f"\nResponse data: {response.data}"
            self.fail(error_msg)
    
    def assert_response_structure(self, response, expected_keys):
        """Assert response has expected structure"""
        if isinstance(response.data, list):
            if response.data:
                self.assert_response_contains_fields(response.data[0], expected_keys)
        else:
            self.assert_response_contains_fields(response, expected_keys)


class ConcurrencyTestMixin:
    """Mixin for testing concurrent operations"""
    
    def test_concurrent_access(self, operation, num_threads=5):
        """Test concurrent access to an operation"""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                result = operation()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return results, errors
    
    def assert_race_condition_safe(self, operation, num_threads=5):
        """Assert that operation is safe from race conditions"""
        results, errors = self.test_concurrent_access(operation, num_threads)
        
        # Check that no errors occurred
        self.assertEqual(len(errors), 0, f"Errors in concurrent access: {errors}")
        
        # Check that all operations completed
        self.assertEqual(len(results), num_threads, f"Expected {num_threads} results, got {len(results)}")


class CustomAssertionsMixin:
    """Mixin providing custom assertions for domain-specific testing"""
    
    def assert_valid_student(self, student):
        """Assert that student object is valid"""
        self.assertIsNotNone(student.user)
        self.assertIsNotNone(student.roll_number)
        self.assertIsNotNone(student.class_grade)
        self.assertIn(student.status, ['active', 'inactive'])
    
    def assert_valid_teacher(self, teacher):
        """Assert that teacher object is valid"""
        self.assertIsNotNone(teacher.user)
        self.assertIsNotNone(teacher.employee_id)
        self.assertIsNotNone(teacher.subject_specialization)
        self.assertIn(teacher.status, ['active', 'inactive'])
    
    def assert_valid_csv_response(self, response):
        """Assert that CSV response is valid"""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('filename=', response['Content-Disposition'])
    
    def assert_valid_pagination(self, response_data):
        """Assert that pagination data is valid"""
        self.assertIn('count', response_data)
        self.assertIn('next', response_data)
        self.assertIn('previous', response_data)
        self.assertIn('results', response_data)
        self.assertIsInstance(response_data['results'], list)


class IntegrationTestMixin:
    """Mixin for integration testing utilities"""
    
    def create_full_workflow_test(self, workflow_steps):
        """Test a complete workflow with multiple steps"""
        context = {}
        
        for step_name, step_function in workflow_steps.items():
            try:
                context = step_function(context)
                self.assertIsNotNone(context, f"Step {step_name} returned None context")
            except Exception as e:
                self.fail(f"Step {step_name} failed with error: {e}")
        
        return context
    
    def assert_end_to_end_flow(self, start_state, end_state, operations):
        """Assert end-to-end flow from start to end state"""
        current_state = start_state
        
        for operation in operations:
            current_state = operation(current_state)
        
        self.assertEqual(current_state, end_state)


# Test decorators
def skip_if_no_database(test_func):
    """Skip test if database is not available"""
    from django.test.utils import override_settings
    
    def wrapper(*args, **kwargs):
        try:
            from django.db import connection
            connection.ensure_connection()
            return test_func(*args, **kwargs)
        except Exception:
            return unittest.skip("Database not available")(test_func)
    
    return wrapper


def timeout_test(seconds=30):
    """Decorator to add timeout to tests"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test timed out after {seconds} seconds")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                return test_func(*args, **kwargs)
            finally:
                signal.alarm(0)
        
        return wrapper
    return decorator


def with_temp_media_root(test_func):
    """Decorator to use temporary media root for tests"""
    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                return test_func(*args, **kwargs)
    
    return wrapper


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_large_text(size=1000):
        """Generate large text for testing"""
        return "A" * size
    
    @staticmethod
    def generate_special_characters():
        """Generate text with special characters"""
        return "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    @staticmethod
    def generate_unicode_text():
        """Generate Unicode text for testing"""
        return "测试数据 тест données de test"
    
    @staticmethod
    def generate_sql_injection_strings():
        """Generate SQL injection test strings"""
        return [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; DELETE FROM users; --",
            "' UNION SELECT * FROM users --"
        ]
    
    @staticmethod
    def generate_xss_strings():
        """Generate XSS test strings"""
        return [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src='x' onerror='alert(1)'>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
        ]