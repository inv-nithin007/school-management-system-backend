from django.contrib import admin
from .models import Exam, Question, StudentExam, StudentAnswer

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'total_marks', 'duration_minutes', 'is_active', 'created_at']
    list_filter = ['subject', 'is_active', 'created_at']
    search_fields = ['title', 'subject']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'question_text', 'correct_answer', 'marks']
    list_filter = ['exam', 'correct_answer']
    search_fields = ['question_text', 'exam__title']

@admin.register(StudentExam)
class StudentExamAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'correct_answers', 'total_questions', 'is_passed']
    list_filter = ['is_passed', 'exam']
    search_fields = ['student__first_name', 'student__last_name', 'exam__title']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_exam', 'question', 'selected_answer', 'is_correct']
    list_filter = ['is_correct', 'selected_answer']