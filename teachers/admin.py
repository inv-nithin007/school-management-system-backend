from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'subject', 'experience_years', 'status']
    list_filter = ['status', 'subject', 'experience_years']
    search_fields = ['first_name', 'last_name', 'email', 'subject']
    readonly_fields = ['created_at', 'updated_at', 'user']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Professional Information', {
            'fields': ('subject', 'qualification', 'experience_years', 'salary', 'status')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
