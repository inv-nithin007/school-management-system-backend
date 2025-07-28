

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from students.models import Student
from .models import Exam, Question, StudentExam, StudentAnswer
from .serializers import ExamSerializer, QuestionSerializer, StudentExamSerializer, AnswerSubmissionSerializer

class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter exams based on user role"""
        user = self.request.user
        
        try:
            if hasattr(user, 'userprofile'):
                user_role = user.userprofile.role
            else:
                return Exam.objects.none()
        except:
            return Exam.objects.none()
        
        if user_role == 'teacher':
            return Exam.objects.filter(created_by=user)
        elif user_role == 'student':
            try:
                student = Student.objects.get(user=user)
                if student.assigned_teacher:
                    return Exam.objects.filter(created_by=student.assigned_teacher.user)
                else:
                    return Exam.objects.none()
            except Student.DoesNotExist:
                return Exam.objects.none()
        
        return Exam.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Only teachers can create exams"""
        try:
            if hasattr(request.user, 'userprofile'):
                user_role = request.user.userprofile.role
            else:
                return Response({'error': 'No user profile found'}, status=status.HTTP_403_FORBIDDEN)
        except:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            
        if user_role != 'teacher':
            return Response({'error': 'Only teachers can create exams'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start_exam(self, request, pk=None):
        """Students start taking an exam - FIXED UNIQUE CONSTRAINT"""
        exam = self.get_object()
        
        # Verify user is a student
        try:
            if hasattr(request.user, 'userprofile'):
                user_role = request.user.userprofile.role
            else:
                return Response({'error': 'No user profile found'}, status=status.HTTP_403_FORBIDDEN)
        except:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if user_role != 'student':
            return Response({'error': 'Only students can take exams'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get student profile
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create StudentExam record - THIS FIXES THE UNIQUE CONSTRAINT ERROR
        student_exam, created = StudentExam.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={
                'total_questions': exam.questions.count(),
                'score': 0,
                'correct_answers': 0,
                'is_passed': False
            }
        )
        
        # Check if exam was already completed
        if student_exam.completed_at:
            return Response({
                'error': 'You have already completed this exam',
                'score': student_exam.score,
                'total_marks': exam.total_marks,
                'completed_at': student_exam.completed_at
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # If record existed but was incomplete, reset it for fresh start
        if not created:
            student_exam.started_at = timezone.now()
            student_exam.score = 0
            student_exam.correct_answers = 0
            student_exam.is_passed = False
            student_exam.total_questions = exam.questions.count()
            student_exam.save()
            
            # Clear any existing answers
            StudentAnswer.objects.filter(student_exam=student_exam).delete()
        
        # Get questions
        questions = []
        exam_questions = exam.questions.all()
        
        if not exam_questions.exists():
            return Response({'error': 'This exam has no questions'}, status=status.HTTP_400_BAD_REQUEST)
        
        for q in exam_questions:
            question_data = {
                'id': q.id,
                'question_text': q.question_text,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'marks': q.marks
            }
            questions.append(question_data)
        
        return Response({
            'message': 'Exam started successfully',
            'exam_title': exam.title,
            'duration_minutes': exam.duration_minutes,
            'total_marks': exam.total_marks,
            'questions': questions
        })
    
    @action(detail=True, methods=['post'])
    def submit_exam(self, request, pk=None):
        """Students submit their answers"""
        exam = self.get_object()
        
        # Get student
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create StudentExam record
        student_exam, created = StudentExam.objects.get_or_create(
            student=student,
            exam=exam,
            defaults={
                'total_questions': exam.questions.count(),
                'score': 0,
                'correct_answers': 0,
                'is_passed': False
            }
        )
        
        # If already completed, don't allow resubmission
        if student_exam.completed_at:
            return Response({
                'error': 'Exam already completed',
                'score': student_exam.score,
                'total_marks': exam.total_marks,
                'completed_at': student_exam.completed_at
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate request data
        if 'answers' not in request.data:
            return Response({'error': 'No answers provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        answers_data = request.data['answers']
        if not isinstance(answers_data, list):
            return Response({'error': 'Answers must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Clear any existing answers for this attempt (in case of resubmission)
        StudentAnswer.objects.filter(student_exam=student_exam).delete()
        
        # Process answers
        total_score = 0
        correct_count = 0
        
        for answer in answers_data:
            if not isinstance(answer, dict) or 'question_id' not in answer or 'selected_answer' not in answer:
                continue
                
            if answer['selected_answer'] not in ['A', 'B', 'C', 'D']:
                continue
            
            try:
                question = Question.objects.get(id=answer['question_id'], exam=exam)
                is_correct = question.correct_answer == answer['selected_answer']
                
                # Save student answer
                StudentAnswer.objects.create(
                    student_exam=student_exam,
                    question=question,
                    selected_answer=answer['selected_answer'],
                    is_correct=is_correct
                )
                
                if is_correct:
                    total_score += question.marks
                    correct_count += 1
                    
            except Question.DoesNotExist:
                continue
        
        # Update student exam - ONLY mark as completed when actually submitting
        student_exam.score = total_score
        student_exam.correct_answers = correct_count
        student_exam.is_passed = total_score >= exam.passing_marks
        student_exam.completed_at = timezone.now()  # Only set this when actually submitting
        student_exam.total_questions = exam.questions.count()  # Update this too
        student_exam.save()
        
        return Response({
            'message': 'Exam submitted successfully',
            'score': total_score,
            'total_marks': exam.total_marks,
            'correct_answers': correct_count,
            'total_questions': student_exam.total_questions,
            'is_passed': student_exam.is_passed
        })

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        try:
            if hasattr(user, 'userprofile') and user.userprofile.role == 'teacher':
                return Question.objects.filter(exam__created_by=user)
        except:
            pass
        return Question.objects.none()
    
    def create(self, request, *args, **kwargs):
        try:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher':
                return super().create(request, *args, **kwargs)
        except:
            pass
        return Response({'error': 'Only teachers can create questions'}, status=status.HTTP_403_FORBIDDEN)

class StudentExamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentExam.objects.all()
    serializer_class = StudentExamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            student = Student.objects.get(user=self.request.user)
            return StudentExam.objects.filter(student=student)
        except Student.DoesNotExist:
            return StudentExam.objects.none()
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        student_exam = self.get_object()
        
        if not student_exam.completed_at:
            return Response({'error': 'Exam not completed yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        answers = []
        for answer in StudentAnswer.objects.filter(student_exam=student_exam):
            answers.append({
                'question': answer.question.question_text,
                'selected_answer': answer.selected_answer,
                'correct_answer': answer.question.correct_answer,
                'is_correct': answer.is_correct
            })
        
        return Response({
            'exam_title': student_exam.exam.title,
            'score': student_exam.score,
            'total_marks': student_exam.exam.total_marks,
            'is_passed': student_exam.is_passed,
            'completed_at': student_exam.completed_at,
            'answers': answers
        })
