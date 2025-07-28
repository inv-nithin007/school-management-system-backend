from django.test import TestCase
from django.contrib.auth.models import User
from .models import Exam, Question, StudentExam, StudentAnswer
from .serializers import ExamSerializer, QuestionSerializer, StudentExamSerializer, StudentAnswerSerializer, ExamSubmissionSerializer
from students.models import Student


class ExamSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )

    def test_exam_serializer_valid_data(self):
        data = {
            'title': 'Math Test',
            'description': 'Basic math test',
            'subject': 'Mathematics',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 40
        }
        
        serializer = ExamSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_exam_serializer_missing_title(self):
        data = {
            'description': 'Basic math test',
            'subject': 'Mathematics',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 40
        }
        
        serializer = ExamSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_exam_serializer_with_questions(self):
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.user
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
        
        serializer = ExamSerializer(exam)
        self.assertEqual(len(serializer.data['questions']), 1)
        self.assertEqual(serializer.data['question_count'], 1)


class QuestionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )
        
        self.exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.user
        )

    def test_question_serializer_valid_data(self):
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
        
        serializer = QuestionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_question_serializer_missing_question_text(self):
        data = {
            'exam': self.exam.id,
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_answer': 'B'
        }
        
        serializer = QuestionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('question_text', serializer.errors)

    def test_question_serializer_invalid_correct_answer(self):
        data = {
            'exam': self.exam.id,
            'question_text': 'What is 2 + 2?',
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_answer': 'E'
        }
        
        serializer = QuestionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('correct_answer', serializer.errors)


class StudentExamSerializerTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )
        
        self.student_user = User.objects.create_user(
            username='student@example.com',
            password='testpass123',
            email='student@example.com'
        )
        
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
        
        self.exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )

    def test_student_exam_serializer_data(self):
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam,
            score=50,
            is_passed=True
        )
        
        serializer = StudentExamSerializer(student_exam)
        self.assertEqual(serializer.data['exam_title'], 'Math Test')
        self.assertEqual(serializer.data['student_name'], 'John')
        self.assertEqual(serializer.data['score'], 50)
        self.assertTrue(serializer.data['is_passed'])


class StudentAnswerSerializerTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )
        
        self.student_user = User.objects.create_user(
            username='student@example.com',
            password='testpass123',
            email='student@example.com'
        )
        
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
        
        self.exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.teacher_user
        )
        
        self.question = Question.objects.create(
            exam=self.exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B'
        )
        
        self.student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam
        )

    def test_student_answer_serializer_valid_data(self):
        data = {
            'student_exam': self.student_exam.id,
            'question': self.question.id,
            'selected_answer': 'B'
        }
        
        serializer = StudentAnswerSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ExamSubmissionSerializerTest(TestCase):
    def test_exam_submission_serializer_valid_data(self):
        data = {
            'answers': [
                {'question_id': '1', 'selected_answer': 'A'},
                {'question_id': '2', 'selected_answer': 'B'}
            ]
        }
        
        serializer = ExamSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_exam_submission_serializer_empty_answers(self):
        data = {
            'answers': []
        }
        
        serializer = ExamSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('answers', serializer.errors)

    def test_exam_submission_serializer_invalid_answer_format(self):
        data = {
            'answers': [
                {'question_id': '1'},  # Missing selected_answer
                {'selected_answer': 'B'}  # Missing question_id
            ]
        }
        
        serializer = ExamSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('answers', serializer.errors)

    def test_exam_submission_serializer_invalid_selected_answer(self):
        data = {
            'answers': [
                {'question_id': '1', 'selected_answer': 'E'}  # Invalid answer
            ]
        }
        
        serializer = ExamSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('answers', serializer.errors)