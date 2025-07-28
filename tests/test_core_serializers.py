"""
Core serializer tests for School Management System
Basic serializer tests without advanced scenarios
"""
from django.test import TestCase
from rest_framework import serializers

from students.serializers import StudentSerializer, StudentCreateSerializer
from teachers.serializers import TeacherSerializer, TeacherCreateSerializer
from .factories import StudentFactory, TeacherFactory, UserFactory


class CoreStudentSerializerTest(TestCase):
    """Core student serializer tests"""
    
    def setUp(self):
        self.teacher = TeacherFactory()
        self.student = StudentFactory(assigned_teacher=self.teacher)
    
    def test_student_serializer_fields(self):
        """Test student serializer contains expected fields"""
        serializer = StudentSerializer(instance=self.student)
        data = serializer.data
        
        expected_fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_student_serializer_data_types(self):
        """Test serializer data types"""
        serializer = StudentSerializer(instance=self.student)
        data = serializer.data
        
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['first_name'], str)
        self.assertIsInstance(data['last_name'], str)
        self.assertIsInstance(data['email'], str)
        self.assertIsInstance(data['roll_number'], str)
        self.assertIsInstance(data['class_grade'], str)
        self.assertIsInstance(data['status'], str)
    
    def test_student_serializer_validation_success(self):
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
    
    def test_student_serializer_validation_required_fields(self):
        """Test validation of required fields"""
        serializer = StudentSerializer(data={})
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['first_name', 'last_name', 'email', 'roll_number', 'class_grade']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_student_serializer_update(self):
        """Test serializer update functionality"""
        data = {
            'first_name': 'Updated',
            'status': 'inactive'
        }
        
        serializer = StudentSerializer(instance=self.student, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_student = serializer.save()
        self.assertEqual(updated_student.first_name, 'Updated')
        self.assertEqual(updated_student.status, 'inactive')


class CoreTeacherSerializerTest(TestCase):
    """Core teacher serializer tests"""
    
    def setUp(self):
        self.teacher = TeacherFactory()
    
    def test_teacher_serializer_fields(self):
        """Test teacher serializer contains expected fields"""
        serializer = TeacherSerializer(instance=self.teacher)
        data = serializer.data
        
        expected_fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'employee_id', 'subject_specialization', 'date_of_joining',
            'status', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_teacher_serializer_validation_success(self):
        """Test successful data validation"""
        valid_data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice@example.com',
            'phone_number': '9876543210',
            'employee_id': 'T001',
            'subject_specialization': 'Mathematics',
            'date_of_joining': '2024-01-01',
            'status': 'active'
        }
        
        serializer = TeacherSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_teacher_serializer_validation_required_fields(self):
        """Test validation of required fields"""
        serializer = TeacherSerializer(data={})
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['first_name', 'last_name', 'email', 'employee_id', 'subject_specialization']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_teacher_serializer_update(self):
        """Test serializer update functionality"""
        data = {
            'first_name': 'Updated',
            'subject_specialization': 'Physics'
        }
        
        serializer = TeacherSerializer(instance=self.teacher, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_teacher = serializer.save()
        self.assertEqual(updated_teacher.first_name, 'Updated')
        self.assertEqual(updated_teacher.subject_specialization, 'Physics')


class CoreCreateSerializerTest(TestCase):
    """Core create serializer tests"""
    
    def test_student_create_serializer_fields(self):
        """Test student create serializer contains expected fields"""
        serializer = StudentCreateSerializer()
        expected_fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.fields)
    
    def test_student_create_serializer_validation(self):
        """Test student create serializer validation"""
        teacher = TeacherFactory()
        
        valid_data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@example.com',
            'phone_number': '1234567890',
            'roll_number': 'S999',
            'class_grade': '10',
            'date_of_birth': '2005-01-01',
            'admission_date': '2024-01-01',
            'assigned_teacher': teacher.id
        }
        
        serializer = StudentCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_teacher_create_serializer_fields(self):
        """Test teacher create serializer contains expected fields"""
        serializer = TeacherCreateSerializer()
        expected_fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'employee_id', 'subject_specialization', 'date_of_joining', 'status'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.fields)
    
    def test_teacher_create_serializer_validation(self):
        """Test teacher create serializer validation"""
        valid_data = {
            'first_name': 'New',
            'last_name': 'Teacher',
            'email': 'newteacher@example.com',
            'phone_number': '9876543210',
            'employee_id': 'T999',
            'subject_specialization': 'Chemistry',
            'date_of_joining': '2024-01-01'
        }
        
        serializer = TeacherCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())