from rest_framework import serializers
from .models import Student
from teachers.models import Teacher
import re

class StudentSerializer(serializers.ModelSerializer):
    assigned_teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher', 'assigned_teacher_name', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'assigned_teacher_name', 'created_at', 'updated_at']
    
    def get_assigned_teacher_name(self, obj):
        if obj.assigned_teacher:
            return f"{obj.assigned_teacher.first_name} {obj.assigned_teacher.last_name}"
        return None
        
    def validate_email(self, value):
        # Check email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        # Check if email already exists (exclude current instance)
        instance = self.instance
        if instance and instance.email == value:
            return value
        if Student.objects.filter(email=value).exists():
            raise serializers.ValidationError("Student with this email already exists.")
        return value
    
    def validate_roll_number(self, value):
        # Check if roll number already exists (exclude current instance)
        instance = self.instance
        if instance and instance.roll_number == value:
            return value
        if Student.objects.filter(roll_number=value).exists():
            raise serializers.ValidationError("Student with this roll number already exists.")
        return value

class StudentCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=False)
    
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'roll_number', 'class_grade', 'date_of_birth', 'admission_date',
            'status', 'assigned_teacher', 'password'
        ]
        
    def validate_email(self, value):
        # Check email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
            
        if Student.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value
    
    def validate_roll_number(self, value):
        if Student.objects.filter(roll_number=value).exists():
            raise serializers.ValidationError("A student with this roll number already exists.")
        return value
    
    def validate_first_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long.")
        return value
    
    def validate_last_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long.")
        return value
