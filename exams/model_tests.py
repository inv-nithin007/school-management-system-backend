from django.test import TestCase
from django.contrib.auth.models import User
from .models import Exam, Question, StudentExam, StudentAnswer
from students.models import Student


class ExamModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher@example.com',
            password='testpass123',
            email='teacher@example.com'
        )

    def test_create_exam(self):
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.user
        )
        
        self.assertEqual(exam.title, 'Math Test')
        self.assertEqual(exam.description, 'Basic math test')
        self.assertEqual(exam.subject, 'Mathematics')
        self.assertEqual(exam.duration_minutes, 60)
        self.assertEqual(exam.total_marks, 100)
        self.assertEqual(exam.passing_marks, 40)
        self.assertEqual(exam.created_by, self.user)
        self.assertTrue(exam.is_active)
        self.assertEqual(str(exam), 'Math Test')

    def test_exam_default_is_active(self):
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.user
        )
        
        self.assertTrue(exam.is_active)

    def test_exam_inactive(self):
        exam = Exam.objects.create(
            title='Math Test',
            description='Basic math test',
            subject='Mathematics',
            duration_minutes=60,
            total_marks=100,
            passing_marks=40,
            created_by=self.user,
            is_active=False
        )
        
        self.assertFalse(exam.is_active)


class QuestionModelTest(TestCase):
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

    def test_create_question(self):
        question = Question.objects.create(
            exam=self.exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B',
            marks=5
        )
        
        self.assertEqual(question.exam, self.exam)
        self.assertEqual(question.question_text, 'What is 2 + 2?')
        self.assertEqual(question.option_a, '3')
        self.assertEqual(question.option_b, '4')
        self.assertEqual(question.option_c, '5')
        self.assertEqual(question.option_d, '6')
        self.assertEqual(question.correct_answer, 'B')
        self.assertEqual(question.marks, 5)

    def test_question_default_marks(self):
        question = Question.objects.create(
            exam=self.exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B'
        )
        
        self.assertEqual(question.marks, 1)

    def test_question_string_representation(self):
        question = Question.objects.create(
            exam=self.exam,
            question_text='What is 2 + 2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B'
        )
        
        self.assertEqual(str(question), f'Math Test - Q{question.id}')


class StudentExamModelTest(TestCase):
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

    def test_create_student_exam(self):
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam,
            total_questions=5
        )
        
        self.assertEqual(student_exam.student, self.student)
        self.assertEqual(student_exam.exam, self.exam)
        self.assertEqual(student_exam.total_questions, 5)
        self.assertEqual(student_exam.score, 0)
        self.assertEqual(student_exam.correct_answers, 0)
        self.assertFalse(student_exam.is_passed)
        self.assertIsNone(student_exam.completed_at)

    def test_student_exam_default_values(self):
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam
        )
        
        self.assertEqual(student_exam.score, 0)
        self.assertEqual(student_exam.total_questions, 0)
        self.assertEqual(student_exam.correct_answers, 0)
        self.assertFalse(student_exam.is_passed)

    def test_student_exam_passed(self):
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam,
            score=50,
            is_passed=True
        )
        
        self.assertTrue(student_exam.is_passed)
        self.assertEqual(student_exam.score, 50)

    def test_student_exam_string_representation(self):
        student_exam = StudentExam.objects.create(
            student=self.student,
            exam=self.exam
        )
        
        self.assertEqual(str(student_exam), 'John - Math Test')


class StudentAnswerModelTest(TestCase):
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

    def test_create_student_answer(self):
        answer = StudentAnswer.objects.create(
            student_exam=self.student_exam,
            question=self.question,
            selected_answer='B',
            is_correct=True
        )
        
        self.assertEqual(answer.student_exam, self.student_exam)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.selected_answer, 'B')
        self.assertTrue(answer.is_correct)

    def test_student_answer_default_incorrect(self):
        answer = StudentAnswer.objects.create(
            student_exam=self.student_exam,
            question=self.question,
            selected_answer='A'
        )
        
        self.assertFalse(answer.is_correct)

    def test_student_answer_string_representation(self):
        answer = StudentAnswer.objects.create(
            student_exam=self.student_exam,
            question=self.question,
            selected_answer='B'
        )
        
        self.assertEqual(str(answer), f'John - Q{self.question.id}')