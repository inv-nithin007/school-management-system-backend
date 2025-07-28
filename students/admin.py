from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'roll_number', 'class_grade', 'assigned_teacher', 'status']
    list_filter = ['status', 'class_grade', 'assigned_teacher', 'admission_date']
    search_fields = ['first_name', 'last_name', 'email', 'roll_number']
    readonly_fields = ['created_at', 'updated_at', 'user']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')
        }),
        ('Academic Information', {
            'fields': ('roll_number', 'class_grade', 'admission_date', 'assigned_teacher', 'status')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
