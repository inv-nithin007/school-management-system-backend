from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import UserProfile
from .models import Student
from teachers.models import Teacher


class StudentViewTest(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            password='adminpass123',
            email='admin@example.com'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')
        
        # Create student user
        self.student_user = User.objects.create_user(
            username='student@example.com',
            password='studentpass123',
            email='student@example.com'
        )
        UserProfile.objects.create(user=self.student_user, role='student')
        
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher@example.com',
            password='teacherpass123',
            email='teacher@example.com'
        )
        UserProfile.objects.create(user=self.teacher_user, role='teacher')
        
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='Test',
            last_name='Teacher',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Math'
        )

    def test_create_student_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('student-list')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Student.objects.filter(roll_number='STU001').exists())

    def test_create_student_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('student-list')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '9876543210',
            'roll_number': 'STU001',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2020-04-01'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_students(self):
        self.client.force_authenticate(user=self.admin_user)
        
        Student.objects.create(
            user=self.student_user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        url = reverse('student-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_student_detail(self):
        self.client.force_authenticate(user=self.admin_user)
        
        student = Student.objects.create(
            user=self.student_user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')

    def test_update_student(self):
        self.client.force_authenticate(user=self.admin_user)
        
        student = Student.objects.create(
            user=self.student_user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        data = {
            'first_name': 'Johnny',
            'class_grade': '11'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        student.refresh_from_db()
        self.assertEqual(student.first_name, 'Johnny')
        self.assertEqual(student.class_grade, '11')

    def test_delete_student(self):
        self.client.force_authenticate(user=self.admin_user)
        
        student = Student.objects.create(
            user=self.student_user,
            first_name='John',
            last_name='Doe',
            email='student@example.com',
            phone_number='9876543210',
            roll_number='STU001',
            class_grade='10',
            date_of_birth='2005-01-01',
            admission_date='2020-04-01'
        )
        
        url = reverse('student-detail', kwargs={'pk': student.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())

    def test_csv_import_success(self):
        self.client.force_authenticate(user=self.admin_user)
        
        csv_data = """first_name,last_name,email,phone_number,roll_number,class_grade,date_of_birth,admission_date
John,Doe,john@example.com,9876543210,STU001,10,2005-01-01,2020-04-01
Jane,Smith,jane@example.com,9876543211,STU002,10,2005-02-01,2020-04-01"""
        
        csv_content = csv_data.encode('utf-8')
        csv_file = SimpleUploadedFile("students.csv", csv_content, content_type="text/csv")
        
        url = reverse('student-import-csv')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Student.objects.count(), 2)

    def test_csv_import_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        csv_data = """first_name,last_name,email,phone_number,roll_number,class_grade,date_of_birth,admission_date
John,Doe,john@example.com,9876543210,STU001,10,2005-01-01,2020-04-01"""
        
        csv_content = csv_data.encode('utf-8')
        csv_file = SimpleUploadedFile("students.csv", csv_content, content_type="text/csv")
        
        url = reverse('student-import-csv')
        response = self.client.post(url, {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csv_import_invalid_file(self):
        self.client.force_authenticate(user=self.admin_user)
        
        invalid_file = SimpleUploadedFile("invalid.txt", b'invalid content', content_type="text/plain")
        
        url = reverse('student-import-csv')
        response = self.client.post(url, {'file': invalid_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_csv_import_no_file(self):
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('student-import-csv')
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)