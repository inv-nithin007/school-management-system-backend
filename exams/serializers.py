from rest_framework import serializers
from .models import Exam, Question, StudentExam, StudentAnswer

# Question Serializer - Handle Questions
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ['id']
    
    def validate_question_text(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Question too short")
        return value
    
    def validate_correct_answer(self, value):
        if value not in ['A', 'B', 'C', 'D']:
            raise serializers.ValidationError("Answer must be A, B, C, or D")
        return value

# Exam Serializer - Handle Exams  
class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title too short")
        return value
    
    def validate_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be positive")
        return value

# Student Exam Serializer - Handle Student Attempts
class StudentExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentExam
        fields = '__all__'
        read_only_fields = ['id', 'started_at', 'completed_at', 'score', 'is_passed']

# Answer Submission Serializer - Validate Student Answers
class AnswerSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListField()
    
    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Need at least one answer")
        
        for answer in value:
            if 'question_id' not in answer or 'selected_answer' not in answer:
                raise serializers.ValidationError("Missing question_id or selected_answer")
            
            if answer['selected_answer'] not in ['A', 'B', 'C', 'D']:
                raise serializers.ValidationError("Answer must be A, B, C, or D")
        
        return value