from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import UserProfile
from .models import Teacher


class TeacherViewTest(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            password='adminpass123',
            email='admin@example.com'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher@example.com',
            password='teacherpass123',
            email='teacher@example.com'
        )
        UserProfile.objects.create(user=self.teacher_user, role='teacher')
        
        # Create student user
        self.student_user = User.objects.create_user(
            username='student@example.com',
            password='studentpass123',
            email='student@example.com'
        )
        UserProfile.objects.create(user=self.student_user, role='student')

    def test_create_teacher_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-list')
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics',
            'qualification': 'M.Sc Mathematics',
            'experience_years': 5,
            'salary': 50000.00
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Teacher.objects.filter(email='john.smith@example.com').exists())

    def test_create_teacher_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teacher-list')
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@example.com',
            'phone_number': '1234567890',
            'subject': 'Mathematics'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_teachers(self):
        self.client.force_authenticate(user=self.admin_user)
        
        Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_teacher_detail(self):
        self.client.force_authenticate(user=self.admin_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')

    def test_update_teacher_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        data = {
            'first_name': 'Johnny',
            'subject': 'Physics'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        teacher.refresh_from_db()
        self.assertEqual(teacher.first_name, 'Johnny')
        self.assertEqual(teacher.subject, 'Physics')

    def test_update_teacher_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        data = {
            'first_name': 'Johnny'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_teacher_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Teacher.objects.filter(pk=teacher.pk).exists())

    def test_delete_teacher_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-detail', kwargs={'pk': teacher.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_students_endpoint(self):
        self.client.force_authenticate(user=self.admin_user)
        
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name='John',
            last_name='Smith',
            email='teacher@example.com',
            phone_number='1234567890',
            subject='Mathematics'
        )
        
        url = reverse('teacher-students', kwargs={'pk': teacher.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_teacher_missing_fields(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('teacher-list')
        data = {
            'first_name': 'John',
            'last_name': 'Smith'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)