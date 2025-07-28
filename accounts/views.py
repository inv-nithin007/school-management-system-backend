from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, PasswordResetToken
# Import the profile models
from students.models import Student
from teachers.models import Teacher

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            
            # IMPROVED: Get user role with superuser detection
            user_role = 'student'  # default
            
            # Check if user is superuser first
            if user.is_superuser:
                user_role = 'admin'
                # Ensure superuser has admin profile
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'admin'}
                )
                if not created and profile.role != 'admin':
                    profile.role = 'admin'
                    profile.save()
            elif hasattr(user, 'userprofile'):
                user_role = user.userprofile.role
            else:
                # Create default profile for users without one
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'student'}
                )
            
            # Base user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user_role,
            }
            
            # Add role-specific profile data
            if user_role == 'student':
                try:
                    student = Student.objects.get(user=user)
                    user_data.update({
                        'roll_number': student.roll_number,
                        'class_grade': student.class_grade,
                        'phone_number': student.phone_number,
                        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else None,
                        'admission_date': student.admission_date.strftime('%Y-%m-%d') if student.admission_date else None,
                        'status': student.status,
                        'assigned_teacher_id': student.assigned_teacher.id if student.assigned_teacher else None,
                        'assigned_teacher_name': f"{student.assigned_teacher.first_name} {student.assigned_teacher.last_name}" if student.assigned_teacher else None,
                        'assigned_teacher_email': student.assigned_teacher.email if student.assigned_teacher else None,
                        'assigned_teacher_phone': student.assigned_teacher.phone_number if student.assigned_teacher else None,
                        'assigned_teacher_subject': getattr(student.assigned_teacher, 'subject', None) if student.assigned_teacher else None,
                        'assigned_teacher_qualification': getattr(student.assigned_teacher, 'qualification', None) if student.assigned_teacher else None,
                        'assigned_teacher_experience': getattr(student.assigned_teacher, 'experience_years', None) if student.assigned_teacher else None,
                    })
                except Student.DoesNotExist:
                    # If student profile doesn't exist, add null values
                    user_data.update({
                        'roll_number': None,
                        'class_grade': None,
                        'phone_number': None,
                        'date_of_birth': None,
                        'admission_date': None,
                        'status': None,
                        'assigned_teacher_id': None,
                        'assigned_teacher_name': None,
                        'assigned_teacher_email': None,
                        'assigned_teacher_phone': None,
                        'assigned_teacher_subject': None,
                        'assigned_teacher_qualification': None,
                        'assigned_teacher_experience': None,
                    })
                    
            elif user_role == 'teacher':
                try:
                    teacher = Teacher.objects.get(user=user)
                    # Count assigned students
                    students_count = Student.objects.filter(assigned_teacher=teacher).count()
                    
                    user_data.update({
                        'phone_number': teacher.phone_number,
                        'subject': getattr(teacher, 'subject', getattr(teacher, 'subject_specialization', None)),
                        'qualification': getattr(teacher, 'qualification', None),
                        'experience_years': getattr(teacher, 'experience_years', None),
                        'salary': float(teacher.salary) if hasattr(teacher, 'salary') and teacher.salary else None,
                        'status': teacher.status,
                        'students_count': students_count,
                    })
                except Teacher.DoesNotExist:
                    # If teacher profile doesn't exist, add null values
                    user_data.update({
                        'phone_number': None,
                        'subject': None,
                        'qualification': None,
                        'experience_years': None,
                        'salary': None,
                        'status': None,
                        'students_count': 0,
                    })
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
        else:
            return Response({'error': 'Invalid credentials'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        role = request.data.get('role', 'student')
        
        if not all([username, password, email]):
            return Response({'error': 'Username, password, and email are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        UserProfile.objects.create(user=user, role=role)
        
        refresh = RefreshToken.for_user(user)
        
        # Build complete user data for registration response
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
        }
        
        # Add default null values for profile data
        if role == 'student':
            user_data.update({
                'roll_number': None,
                'class_grade': None,
                'phone_number': None,
                'date_of_birth': None,
                'admission_date': None,
                'status': None,
                'assigned_teacher_id': None,
                'assigned_teacher_name': None,
                'assigned_teacher_email': None,
                'assigned_teacher_phone': None,
                'assigned_teacher_subject': None,
                'assigned_teacher_qualification': None,
                'assigned_teacher_experience': None,
            })
        elif role == 'teacher':
            user_data.update({
                'phone_number': None,
                'subject': None,
                'qualification': None,
                'experience_years': None,
                'salary': None,
                'status': None,
                'students_count': 0,
            })
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send password reset email to user"""
    try:
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists - Handle multiple users with same email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except User.MultipleObjectsReturned:
            # Handle duplicate emails - use the first active user
            users = User.objects.filter(email=email, is_active=True)
            if users.exists():
                user = users.first()
            else:
                return Response(
                    {'error': 'Multiple accounts found with this email. Please contact admin.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Delete old tokens for this user
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Create new reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Send email
        subject = 'Password Reset Request - School Management System'
        message = f"""
Hello {user.first_name or user.username},

You have requested to reset your password for School Management System.

Please click the link below to reset your password:
http://localhost:5173/reset/{reset_token.token}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
School Management System Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Password reset email sent successfully. Please check your email.'
            })
            
        except Exception as email_error:
            return Response(
                {'error': f'Failed to send email: {str(email_error)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using token"""
    try:
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response(
                {'error': 'Token and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password length
        if len(new_password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find reset token
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid reset token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is valid
        if not reset_token.is_valid():
            return Response(
                {'error': 'Reset token has expired or already been used'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset the password
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        return Response({
            'message': 'Password reset successfully. You can now login with your new password.'
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for logged-in users"""
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        # Check if both passwords are provided
        if not current_password or not new_password:
            return Response(
                {'error': 'Current password and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password is long enough
        if len(new_password) < 6:
            return Response(
                {'error': 'New password must be at least 6 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if current password is correct
        user = request.user
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password is different from current password
        if user.check_password(new_password):
            return Response(
                {'error': 'New password must be different from current password'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Change the password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully. Please login again with your new password.'
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
