from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import transaction
from .models import Student
from .serializers import StudentSerializer, StudentCreateSerializer
import csv
import io
import logging

logger = logging.getLogger(__name__)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('user', 'assigned_teacher').all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'class_grade', 'assigned_teacher']
    search_fields = ['first_name', 'last_name', 'email', 'roll_number']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StudentCreateSerializer
        return StudentSerializer
    
    def check_admin_permission(self, request):
        """Check if the user has admin permissions"""
        try:
            if hasattr(request.user, 'userprofile'):
                user_role = request.user.userprofile.role
                return user_role == 'admin'
            return request.user.is_superuser
        except Exception as e:
            logger.error(f"Error checking admin permission: {e}")
            return False
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        try:
            if hasattr(user, 'userprofile'):
                user_role = user.userprofile.role
                
                if user_role == 'admin':
                    return Student.objects.select_related('user', 'assigned_teacher').all()
                elif user_role == 'teacher':
                    # Teachers can see their assigned students
                    try:
                        from teachers.models import Teacher
                        teacher = Teacher.objects.get(user=user)
                        return Student.objects.filter(assigned_teacher=teacher).select_related('user', 'assigned_teacher')
                    except Teacher.DoesNotExist:
                        return Student.objects.none()
                elif user_role == 'student':
                    # Students can only see themselves
                    try:
                        student = Student.objects.get(user=user)
                        return Student.objects.filter(id=student.id).select_related('user', 'assigned_teacher')
                    except Student.DoesNotExist:
                        return Student.objects.none()
            elif user.is_superuser:
                return Student.objects.select_related('user', 'assigned_teacher').all()
        except Exception as e:
            logger.error(f"Error in get_queryset: {e}")
        
        return Student.objects.none()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new student (admin only)"""
        # Check if user is admin
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Only admins can create students'}, 
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
            
            # Check if user with email already exists
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'A user with this email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create user with admin-provided password
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                password=password
            )
            
            # Import UserProfile here to avoid circular imports
            from accounts.models import UserProfile
            UserProfile.objects.create(user=user, role='student')
            
            # Remove password from validated_data before creating student
            student_data = serializer.validated_data.copy()
            student_data.pop('password', None)
            
            # Create student
            student = Student.objects.create(user=user, **student_data)
            
            # Return success response
            response_serializer = StudentSerializer(student)
            response_data = response_serializer.data
            response_data['message'] = 'Student created successfully.'
            
            logger.info(f"Student created successfully: {student.email}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update an existing student"""
        try:
            # Check permissions (admin or the student themselves)
            instance = self.get_object()
            
            if not (self.check_admin_permission(request) or 
                   (hasattr(request.user, 'userprofile') and 
                    request.user.userprofile.role == 'student' and 
                    instance.user == request.user)):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Update related User model fields
            user_data = {}
            for field in ['first_name', 'last_name', 'email']:
                if field in serializer.validated_data:
                    user_data[field] = serializer.validated_data[field]
            
            # If email is being updated, also update username
            if 'email' in user_data:
                # Check if email is already taken by another user
                email = user_data['email']
                existing_user = User.objects.filter(email=email).exclude(id=instance.user.id)
                if existing_user.exists():
                    return Response(
                        {'error': 'A user with this email already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user_data['username'] = email
            
            # Update user fields if any
            if user_data:
                User.objects.filter(id=instance.user.id).update(**user_data)
                # Refresh the user instance
                instance.user.refresh_from_db()
            
            # Save the student instance
            serializer.save()
            
            logger.info(f"Student updated successfully: {instance.email}")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating student: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a student (admin only)"""
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Only admins can delete students'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = self.get_object()
            # Delete the associated user (this will cascade to student)
            user = instance.user
            instance.delete()
            user.delete()
            
            logger.info(f"Student deleted successfully: {instance.email}")
            return Response({'message': 'Student deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error deleting student: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get detailed student profile"""
        try:
            student = self.get_object()
            
            # Check permissions
            if not (self.check_admin_permission(request) or 
                   (hasattr(request.user, 'userprofile') and 
                    request.user.userprofile.role == 'teacher' and 
                    student.assigned_teacher and 
                    student.assigned_teacher.user == request.user) or
                   (hasattr(request.user, 'userprofile') and 
                    request.user.userprofile.role == 'student' and 
                    student.user == request.user)):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = StudentSerializer(student)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting student profile: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export all students to CSV file (admin only)"""
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Only admins can export data'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="students.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'ID', 'First Name', 'Last Name', 'Email', 'Phone Number',
                'Roll Number', 'Class Grade', 'Date of Birth', 'Admission Date',
                'Status', 'Assigned Teacher', 'Created At', 'Updated At'
            ])
            
            # Write data
            for student in self.get_queryset():
                assigned_teacher = (
                    f"{student.assigned_teacher.first_name} {student.assigned_teacher.last_name}" 
                    if student.assigned_teacher else 'None'
                )
                
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
                    assigned_teacher,
                    student.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    student.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            logger.info("Students CSV export completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error exporting students CSV: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """Import students from CSV file (admin only)"""
        if not self.check_admin_permission(request):
            return Response(
                {'error': 'Only admins can import students'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES['file']
        
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read CSV file
            file_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Check required columns
            required_columns = [
                'first_name', 'last_name', 'email', 'phone_number', 
                'roll_number', 'class_grade', 'date_of_birth', 'admission_date'
            ]
            
            fieldnames = csv_reader.fieldnames or []
            missing_columns = [col for col in required_columns if col not in fieldnames]
            if missing_columns:
                return Response(
                    {'error': f'Missing required columns: {", ".join(missing_columns)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success_count = 0
            errors = []
            
            # Import UserProfile here to avoid circular imports
            from accounts.models import UserProfile
            
            with transaction.atomic():
                for index, row in enumerate(csv_reader, start=2):  # Start from 2 because row 1 is header
                    try:
                        # Validate required fields
                        email = row.get('email', '').strip()
                        roll_number = row.get('roll_number', '').strip()
                        
                        if not email:
                            errors.append(f"Row {index}: Email is required")
                            continue
                        
                        if not roll_number:
                            errors.append(f"Row {index}: Roll number is required")
                            continue
                        
                        # Check if user already exists
                        if User.objects.filter(email=email).exists():
                            errors.append(f"Row {index}: Email {email} already exists")
                            continue
                        
                        if Student.objects.filter(roll_number=roll_number).exists():
                            errors.append(f"Row {index}: Roll number {roll_number} already exists")
                            continue
                        
                        # Use password from CSV if provided, otherwise default
                        password = row.get('password', 'student123').strip()
                        if len(password) < 6:
                            password = 'student123'
                        
                        # Create user
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            first_name=row.get('first_name', '').strip(),
                            last_name=row.get('last_name', '').strip(),
                            password=password
                        )
                        
                        # Create user profile
                        UserProfile.objects.create(user=user, role='student')
                        
                        # Handle assigned teacher
                        assigned_teacher = None
                        assigned_teacher_email = row.get('assigned_teacher_email', '').strip()
                        if assigned_teacher_email:
                            try:
                                from teachers.models import Teacher
                                assigned_teacher = Teacher.objects.get(email=assigned_teacher_email)
                            except Teacher.DoesNotExist:
                                errors.append(f"Row {index}: Assigned teacher with email {assigned_teacher_email} not found")
                        
                        # Create student
                        Student.objects.create(
                            user=user,
                            first_name=row.get('first_name', '').strip(),
                            last_name=row.get('last_name', '').strip(),
                            email=email,
                            phone_number=row.get('phone_number', '').strip(),
                            roll_number=roll_number,
                            class_grade=row.get('class_grade', '').strip(),
                            date_of_birth=row.get('date_of_birth'),
                            admission_date=row.get('admission_date'),
                            status=row.get('status', 'active').strip(),
                            assigned_teacher=assigned_teacher
                        )
                        
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index}: {str(e)}")
            
            logger.info(f"CSV import completed: {success_count} students imported")
            return Response({
                'message': f'Successfully imported {success_count} students',
                'success_count': success_count,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"Error importing students CSV: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
