from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.http import HttpResponse
from accounts.models import UserProfile
from .models import Teacher
from .serializers import TeacherSerializer, TeacherCreateSerializer
import csv

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'subject']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TeacherCreateSerializer
        return TeacherSerializer
    
    def check_admin_permission(self, request):
        """Check if the user is an admin"""
        if hasattr(request.user, 'userprofile'):
            user_role = request.user.userprofile.role
            if user_role == 'admin':
                return True
        return False
    
    def create(self, request, *args, **kwargs):
        # Check if user is admin
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Only admins can create teachers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get password from request
            password = request.data.get('password')
            if not password:
                return Response(
                    {'error': 'Password is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate password length
            if len(password) < 6:
                return Response(
                    {'error': 'Password must be at least 6 characters long'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create user with admin-provided password
            user = User.objects.create_user(
                username=serializer.validated_data['email'],
                email=serializer.validated_data['email'],
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                password=password  # Use admin-provided password
            )
            
            UserProfile.objects.create(user=user, role='teacher')
            
            # Remove password from validated_data before creating teacher
            teacher_data = serializer.validated_data.copy()
            teacher_data.pop('password', None)
            teacher = Teacher.objects.create(user=user, **teacher_data)
            
            response_data = TeacherSerializer(teacher).data
            response_data['message'] = 'Teacher created successfully.'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            user_data = {}
            for field in ['first_name', 'last_name', 'email']:
                if field in serializer.validated_data:
                    user_data[field] = serializer.validated_data[field]
            
            if 'email' in user_data:
                user_data['username'] = user_data['email']
            
            if user_data:
                User.objects.filter(id=instance.user.id).update(**user_data)
            
            serializer.save()
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        try:
            teacher = self.get_object()
            students = teacher.student_set.all()
            from students.serializers import StudentSerializer
            return Response(StudentSerializer(students, many=True).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Export all teachers to CSV file
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="teachers.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'ID', 'First Name', 'Last Name', 'Email', 'Phone Number',
            'Subject', 'Qualification', 'Experience Years', 'Salary',
            'Status', 'Students Count', 'Created At', 'Updated At'
        ])
        
        # Write data
        for teacher in Teacher.objects.all():
            writer.writerow([
                teacher.id,
                teacher.first_name,
                teacher.last_name,
                teacher.email,
                teacher.phone_number,
                teacher.subject,
                teacher.qualification,
                teacher.experience_years,
                teacher.salary,
                teacher.status,
                teacher.student_set.count(),
                teacher.created_at,
                teacher.updated_at
            ])
        
        return response
