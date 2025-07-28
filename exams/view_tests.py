from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import UserProfile
from students.models import Student
from .models import Exam, Question, StudentExam, StudentAnswer


class ExamViewTest(APITestCase):
    def setUp(self):
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
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            password='adminpass123',
            email='admin@example.com'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')
        
        # Create student object
        self.student = Student.objects.create(
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

    def test_create_exam_as_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('exam-list')
        data = {
            'title': 'Math Test',
            'description': 'Basic math test',
            'subject': 'Mathematics',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 40
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Exam.objects.filter(title='Math Test').exists())

    def test_create_exam_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('exam-list')
        data = {
            'title': 'Math Test',
            'description': 'Basic math test',
            'subject': 'Mathematics',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 40
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_exam_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('exam-list')
        data = {
            'title': 'Math Test',
            'description': 'Basic math test',
            'subject': 'Mathematics',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 40
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_exams(self):
        self.client.force_authenticate(user=self.teacher_user)
        
        Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        url = reverse('exam-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_start_exam_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        Question.objects.create(
            exam=exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B'
        )
        
        url = reverse('exam-start-exam', kwargs={'pk': exam.pk})
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(StudentExam.objects.filter(student=self.student, exam=exam).exists())

    def test_start_exam_already_taken(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        # Create existing student exam
        StudentExam.objects.create(
            student=self.student,
            exam=exam
        )
        
        url = reverse('exam-start-exam', kwargs={'pk': exam.pk})
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_exam_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        question = Question.objects.create(
            exam=exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B',
            marks=100
        )
        
        # Start exam
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=exam,
            total_questions=1
        )
        
        # Submit exam
        url = reverse('exam-submit-exam', kwargs={'pk': exam.pk})
        data = {
            'answers': [
                {'question_id': question.id, 'selected_answer': 'B'}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check results
        student_exam.refresh_from_db()
        self.assertEqual(student_exam.score, 100)
        self.assertTrue(student_exam.is_passed)

    def test_submit_exam_already_submitted(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        # Create already completed exam
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=exam
        )
        student_exam.completed_at = student_exam.started_at
        student_exam.save()
        
        url = reverse('exam-submit-exam', kwargs={'pk': exam.pk})
        data = {
            'answers': [
                {'question_id': '1', 'selected_answer': 'B'}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_exam_result(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        question = Question.objects.create(
            exam=exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B',
            marks=100
        )
        
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=exam,
            total_questions=1,
            score=100,
            correct_answers=1,
            is_passed=True
        )
        student_exam.completed_at = student_exam.started_at
        student_exam.save()
        
        StudentAnswer.objects.create(
            student_exam=student_exam,
            question=question,
            selected_answer='B',
            is_correct=True
        )
        
        url = reverse('studentexam-result', kwargs={'pk': student_exam.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 100)
        self.assertTrue(response.data['is_passed'])

    def test_get_exam_result_not_completed(self):
        self.client.force_authenticate(user=self.student_user)
        
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=exam
        )
        
        url = reverse('studentexam-result', kwargs={'pk': student_exam.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuestionViewTest(APITestCase):
    def setUp(self):
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
        
        self.exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )

    def test_create_question_as_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('question-list')
        data = {
            'exam': self.exam.id,
            'question_text': 'What is 2 + 2?',
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_answer': 'B',
            'marks': 5
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Question.objects.filter(question_text='What is 2 + 2?').exists())

    def test_create_question_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('question-list')
        data = {
            'exam': self.exam.id,
            'question_text': 'What is 2 + 2?',
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_answer': 'B'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)