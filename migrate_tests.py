#!/usr/bin/env python
"""
Script to migrate from old basic tests to new industrial-level tests
"""
import os
import shutil
from pathlib import Path

def backup_old_tests():
    """Backup old tests before replacement"""
    print("Creating backup of old tests...")
    
    test_files = [
        'students/tests.py',
        'teachers/tests.py', 
        'accounts/tests.py',
        'school_management/tests.py'
    ]
    
    backup_dir = Path('tests/old_tests_backup')
    backup_dir.mkdir(exist_ok=True)
    
    for test_file in test_files:
        if Path(test_file).exists():
            app_name = test_file.split('/')[0]
            backup_file = backup_dir / f"{app_name}_old_tests.py"
            shutil.copy2(test_file, backup_file)
            print(f"Backed up {test_file} to {backup_file}")

def create_new_app_tests():
    """Create new industrial-level tests for each app"""
    
    # Students app tests
    students_test_content = '''"""
Industrial-level tests for Students app
Import from centralized test suite
"""
from tests.test_student_models import *
from tests.test_student_views import *
from tests.test_student_serializers import *

# Re-export for Django test discovery
__all__ = [
    'StudentModelTest',
    'StudentModelTransactionTest', 
    'StudentModelConcurrencyTest',
    'StudentModelPerformanceTest',
    'StudentViewSetTest',
    'StudentViewPermissionTest',
    'StudentSerializerTest',
    'StudentCreateSerializerTest',
    'StudentSerializerEdgeCasesTest',
    'StudentSerializerIntegrationTest',
]
'''
    
    # Teachers app tests
    teachers_test_content = '''"""
Industrial-level tests for Teachers app
These tests are included in the centralized test suite
"""
from tests.test_integration import *
from tests.factories import TeacherFactory, BatchTeacherFactory
from tests.utils import BaseAPITestCase
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from teachers.models import Teacher

class TeacherModelTest(TestCase):
    """Basic teacher model tests - comprehensive tests in tests/ directory"""
    
    def test_teacher_creation(self):
        """Test teacher creation using factory"""
        teacher = TeacherFactory()
        self.assertIsNotNone(teacher.id)
        self.assertEqual(teacher.status, 'active')
    
    def test_teacher_string_representation(self):
        """Test teacher string representation"""
        teacher = TeacherFactory(first_name='John', last_name='Doe', employee_id='T001')
        self.assertEqual(str(teacher), 'John Doe - T001')

class TeacherAPITest(BaseAPITestCase):
    """Basic teacher API tests - comprehensive tests in tests/ directory"""
    
    def setUp(self):
        super().setUp()
        self.teacher = TeacherFactory()
    
    def test_teacher_list_requires_auth(self):
        """Test that teacher list requires authentication"""
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
'''
    
    # Accounts app tests
    accounts_test_content = '''"""
Industrial-level tests for Accounts app
These tests are included in the centralized test suite
"""
from tests.test_integration import *
from tests.factories import UserFactory, AdminUserFactory
from tests.utils import BaseAPITestCase
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import UserProfile

class UserProfileModelTest(TestCase):
    """Basic user profile tests - comprehensive tests in tests/ directory"""
    
    def test_user_profile_creation(self):
        """Test user profile creation"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.role, 'student')
    
    def test_user_profile_string_representation(self):
        """Test user profile string representation"""
        user = UserFactory(username='testuser')
        profile = UserProfile.objects.create(user=user, role='student')
        self.assertEqual(str(profile), 'testuser - student')

class AuthenticationAPITest(BaseAPITestCase):
    """Basic authentication tests - comprehensive tests in tests/ directory"""
    
    def test_login_requires_credentials(self):
        """Test that login requires credentials"""
        url = reverse('login')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
'''
    
    # School management tests
    school_management_test_content = '''"""
Industrial-level tests for School Management
These tests are included in the centralized test suite
"""
from tests.test_integration import *
from tests.utils import BaseAPITestCase
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

class SchoolManagementIntegrationTest(BaseAPITestCase):
    """Integration tests for school management - comprehensive tests in tests/ directory"""
    
    def test_csv_export_requires_auth(self):
        """Test that CSV export requires authentication"""
        url = reverse('export-all-data-csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
'''
    
    # Write new test files
    test_files = {
        'students/tests.py': students_test_content,
        'teachers/tests.py': teachers_test_content,
        'accounts/tests.py': accounts_test_content,
        'school_management/tests.py': school_management_test_content,
    }
    
    print("Creating new industrial-level app tests...")
    for file_path, content in test_files.items():
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Created {file_path}")

def main():
    """Main migration function"""
    print("🔄 Migrating from basic tests to industrial-level tests...")
    print("=" * 60)
    
    # Step 1: Backup old tests
    backup_old_tests()
    
    # Step 2: Create new app tests that import from centralized suite
    create_new_app_tests()
    
    print("\n✅ Migration completed!")
    print("=" * 60)
    print("SUMMARY:")
    print("• Old tests backed up to tests/old_tests_backup/")
    print("• New industrial-level tests created in each app")
    print("• All tests now use the centralized test suite")
    print("• Run 'python run_tests.py all' to execute all tests")
    print("\nRECOMMENDATION:")
    print("• The old backup tests can be deleted after verifying new tests work")
    print("• Use the centralized test suite in tests/ directory for all new tests")

if __name__ == '__main__':
    main()