"""
Core view tests for School Management System
Basic API tests without advanced scenarios
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .factories import StudentFactory, TeacherFactory, AdminUserFactory, UserFactory
from students.models import Student
from teachers.models import Teacher


class CoreStudentViewTest(APITestCase):
    """Core student view tests"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.teacher = TeacherFactory()
        self.student = StudentFactory(assigned_teacher=self.teacher)
    
    def test_student_list_requires_authentication(self):
        """Test that student list requires authentication"""
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_student_list_with_admin_user(self):
        """Test student list with admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_detail_view(self):
        """Test student detail view"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-detail', kwargs={'pk': self.student.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.student.id)
        self.assertEqual(response.data['first_name'], self.student.first_name)
    
    def test_student_create_with_valid_data(self):
        """Test student creation with valid data"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-list')
        
        data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': self.teacher.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.count(), 2)  # Original + new
    
    def test_student_update(self):
        """Test student update"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-detail', kwargs={'pk': self.student.pk})
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
    
    def test_student_delete(self):
        """Test student deletion"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-detail', kwargs={'pk': self.student.pk})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(id=self.student.id).exists())


class CoreTeacherViewTest(APITestCase):
    """Core teacher view tests"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.teacher = TeacherFactory()
    
    def test_teacher_list_requires_authentication(self):
        """Test that teacher list requires authentication"""
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_teacher_list_with_admin_user(self):
        """Test teacher list with admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_teacher_detail_view(self):
        """Test teacher detail view"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-detail', kwargs={'pk': self.teacher.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.teacher.id)
        self.assertEqual(response.data['first_name'], self.teacher.first_name)
    
    def test_teacher_create_with_valid_data(self):
        """Test teacher creation with valid data"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-list')
        
        data = {
            'first_name': 'New',
            'last_name': 'Teacher',
            'email': 'newteacher@example.com',
            'phone_number': '9876543210',
            'employee_id': 'T999',
            'subject_specialization': 'Physics',
            'date_of_joining': '2024-01-01'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Teacher.objects.count(), 2)  # Original + new
    
    def test_teacher_update(self):
        """Test teacher update"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-detail', kwargs={'pk': self.teacher.pk})
        
        data = {
            'first_name': 'Updated',
            'subject_specialization': 'Advanced Mathematics'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
    
    def test_teacher_delete(self):
        """Test teacher deletion"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-detail', kwargs={'pk': self.teacher.pk})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Teacher.objects.filter(id=self.teacher.id).exists())


class CoreCSVExportTest(APITestCase):
    """Core CSV export tests"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.teacher = TeacherFactory()
        self.student = StudentFactory(assigned_teacher=self.teacher)
    
    def test_student_csv_export_requires_auth(self):
        """Test that student CSV export requires authentication"""
        url = reverse('student-export-csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_teacher_csv_export_requires_auth(self):
        """Test that teacher CSV export requires authentication"""
        url = reverse('teacher-export-csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_student_csv_export_with_admin(self):
        """Test student CSV export with admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-export-csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="students.csv"', response['Content-Disposition'])
    
    def test_teacher_csv_export_with_admin(self):
        """Test teacher CSV export with admin user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-export-csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="teachers.csv"', response['Content-Disposition'])


class CorePermissionTest(APITestCase):
    """Core permission tests"""
    
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.teacher_user = TeacherFactory().user
        self.student_user = StudentFactory().user
    
    def test_admin_has_full_access(self):
        """Test admin has full access to all endpoints"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test student endpoints
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test teacher endpoints
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_teacher_has_read_access(self):
        """Test teacher has read access"""
        self.client.force_authenticate(user=self.teacher_user)
        
        # Test student list (should work)
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test teacher list (should work)
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_has_read_access(self):
        """Test student has read access"""
        self.client.force_authenticate(user=self.student_user)
        
        # Test student list (should work)
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test teacher list (should work)
        url = reverse('teacher-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)