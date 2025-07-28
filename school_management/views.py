from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from students.models import Student
from teachers.models import Teacher
import csv
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_all_data_csv(request):
    """
    Export all student and teacher data to a single CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="school_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Type', 'ID', 'First Name', 'Last Name', 'Email', 'Phone Number',
        'Identifier', 'Additional Info', 'Status', 'Created At', 'Updated At'
    ])
    
    # Write student data
    for student in Student.objects.all():
        writer.writerow([
            'Student',
            student.id,
            student.first_name,
            student.last_name,
            student.email,
            student.phone_number,
            student.roll_number,
            f"Grade: {student.class_grade}, DOB: {student.date_of_birth}",
            student.status,
            student.created_at,
            student.updated_at
        ])
    
    # Write teacher data
    for teacher in Teacher.objects.all():
        writer.writerow([
            'Teacher',
            teacher.id,
            teacher.first_name,
            teacher.last_name,
            teacher.email,
            teacher.phone_number,
            teacher.employee_id,
            f"Subject: {teacher.subject_specialization}, Joined: {teacher.date_of_joining}",
            teacher.status,
            teacher.created_at,
            teacher.updated_at
        ])
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_students_detailed_csv(request):
    """
    Export detailed student data to CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'First Name', 'Last Name', 'Email', 'Phone Number',
        'Roll Number', 'Class Grade', 'Date of Birth', 'Admission Date',
        'Status', 'Assigned Teacher Name', 'Teacher Email', 'Teacher Subject',
        'User ID', 'Username', 'Created At', 'Updated At'
    ])
    
    # Write data
    for student in Student.objects.select_related('user', 'assigned_teacher'):
        teacher_name = f"{student.assigned_teacher.first_name} {student.assigned_teacher.last_name}" if student.assigned_teacher else 'Not Assigned'
        teacher_email = student.assigned_teacher.email if student.assigned_teacher else 'N/A'
        teacher_subject = student.assigned_teacher.subject_specialization if student.assigned_teacher else 'N/A'
        
        writer.writerow([
            student.id,
            student.first_name,
            student.last_name,
            student.email,
            student.phone_number,
            student.roll_number,
            student.class_grade,
            student.date_of_birth,
            student.admission_date,
            student.status,
            teacher_name,
            teacher_email,
            teacher_subject,
            student.user.id,
            student.user.username,
            student.created_at,
            student.updated_at
        ])
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_teachers_detailed_csv(request):
    """
    Export detailed teacher data to CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="teachers_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Teacher ID', 'First Name', 'Last Name', 'Email', 'Phone Number',
        'Subject Specialization', 'Employee ID', 'Date of Joining',
        'Status', 'Students Count', 'Student Names', 'User ID', 'Username',
        'Created At', 'Updated At'
    ])
    
    # Write data
    for teacher in Teacher.objects.select_related('user').prefetch_related('student_set'):
        students = teacher.student_set.all()
        student_names = ', '.join([f"{s.first_name} {s.last_name}" for s in students]) if students else 'None'
        
        writer.writerow([
            teacher.id,
            teacher.first_name,
            teacher.last_name,
            teacher.email,
            teacher.phone_number,
            teacher.subject_specialization,
            teacher.employee_id,
            teacher.date_of_joining,
            teacher.status,
            students.count(),
            student_names,
            teacher.user.id,
            teacher.user.username,
            teacher.created_at,
            teacher.updated_at
        ])
    
    return response