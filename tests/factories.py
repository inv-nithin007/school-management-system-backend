"""
Test factories for creating test data objects
Uses factory_boy for clean, maintainable test data creation
"""
import factory
from django.contrib.auth.models import User
from accounts.models import UserProfile
from students.models import Student
from teachers.models import Teacher
from datetime import date, timedelta


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False


class AdminUserFactory(UserFactory):
    """Factory for creating admin users"""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating UserProfile instances"""
    
    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)
    
    user = factory.SubFactory(UserFactory)
    role = 'student'


class AdminProfileFactory(UserProfileFactory):
    """Factory for creating admin profiles"""
    
    user = factory.SubFactory(AdminUserFactory)
    role = 'admin'


class TeacherProfileFactory(UserProfileFactory):
    """Factory for creating teacher profiles"""
    
    role = 'teacher'


class StudentProfileFactory(UserProfileFactory):
    """Factory for creating student profiles"""
    
    role = 'student'


class TeacherFactory(factory.django.DjangoModelFactory):
    """Factory for creating Teacher instances"""
    
    class Meta:
        model = Teacher
        django_get_or_create = ('employee_id',)
    
    user = factory.SubFactory(UserFactory)
    first_name = factory.SelfAttribute('user.first_name')
    last_name = factory.SelfAttribute('user.last_name')
    email = factory.SelfAttribute('user.email')
    phone_number = factory.Faker('phone_number')
    subject_specialization = factory.Faker('random_element', elements=(
        'Mathematics', 'Science', 'English', 'History', 'Geography', 'Physics', 'Chemistry', 'Biology'
    ))
    employee_id = factory.Sequence(lambda n: f'T{n:03d}')
    date_of_joining = factory.Faker('date_between', start_date='-5y', end_date='today')
    status = 'active'
    
    @factory.post_generation
    def create_profile(self, create, extracted, **kwargs):
        if not create:
            return
        TeacherProfileFactory(user=self.user, role='teacher')


class StudentFactory(factory.django.DjangoModelFactory):
    """Factory for creating Student instances"""
    
    class Meta:
        model = Student
        django_get_or_create = ('roll_number',)
    
    user = factory.SubFactory(UserFactory)
    first_name = factory.SelfAttribute('user.first_name')
    last_name = factory.SelfAttribute('user.last_name')
    email = factory.SelfAttribute('user.email')
    phone_number = factory.Faker('phone_number')
    roll_number = factory.Sequence(lambda n: f'S{n:03d}')
    class_grade = factory.Faker('random_element', elements=('6', '7', '8', '9', '10', '11', '12'))
    date_of_birth = factory.Faker('date_between', start_date='-18y', end_date='-6y')
    admission_date = factory.Faker('date_between', start_date='-5y', end_date='today')
    status = 'active'
    assigned_teacher = factory.SubFactory(TeacherFactory)
    
    @factory.post_generation
    def create_profile(self, create, extracted, **kwargs):
        if not create:
            return
        StudentProfileFactory(user=self.user, role='student')


class StudentWithoutTeacherFactory(StudentFactory):
    """Factory for creating Student without assigned teacher"""
    
    assigned_teacher = None


# Trait factories for different scenarios
class InactiveStudentFactory(StudentFactory):
    """Factory for creating inactive students"""
    
    status = 'inactive'


class InactiveTeacherFactory(TeacherFactory):
    """Factory for creating inactive teachers"""
    
    status = 'inactive'


class RecentStudentFactory(StudentFactory):
    """Factory for creating recently admitted students"""
    
    admission_date = factory.LazyFunction(lambda: date.today() - timedelta(days=30))


class SeniorStudentFactory(StudentFactory):
    """Factory for creating senior grade students"""
    
    class_grade = factory.Faker('random_element', elements=('11', '12'))


class JuniorStudentFactory(StudentFactory):
    """Factory for creating junior grade students"""
    
    class_grade = factory.Faker('random_element', elements=('6', '7', '8'))


class ExperiencedTeacherFactory(TeacherFactory):
    """Factory for creating experienced teachers"""
    
    date_of_joining = factory.Faker('date_between', start_date='-10y', end_date='-5y')


class NewTeacherFactory(TeacherFactory):
    """Factory for creating new teachers"""
    
    date_of_joining = factory.Faker('date_between', start_date='-1y', end_date='today')


# Batch factories for creating multiple instances
class BatchUserFactory:
    """Factory for creating multiple users at once"""
    
    @staticmethod
    def create_batch(size=5, **kwargs):
        return UserFactory.create_batch(size, **kwargs)
    
    @staticmethod
    def create_admin_batch(size=3, **kwargs):
        return AdminUserFactory.create_batch(size, **kwargs)


class BatchStudentFactory:
    """Factory for creating multiple students at once"""
    
    @staticmethod
    def create_batch(size=10, **kwargs):
        return StudentFactory.create_batch(size, **kwargs)
    
    @staticmethod
    def create_grade_batch(grade, size=5, **kwargs):
        return StudentFactory.create_batch(size, class_grade=grade, **kwargs)


class BatchTeacherFactory:
    """Factory for creating multiple teachers at once"""
    
    @staticmethod
    def create_batch(size=5, **kwargs):
        return TeacherFactory.create_batch(size, **kwargs)
    
    @staticmethod
    def create_subject_batch(subject, size=3, **kwargs):
        return TeacherFactory.create_batch(size, subject_specialization=subject, **kwargs)


# Complex scenario factories
class ClassroomSetupFactory:
    """Factory for creating a complete classroom setup"""
    
    @staticmethod
    def create_classroom(teacher_count=2, student_count=20):
        """Create a complete classroom with teachers and students"""
        teachers = TeacherFactory.create_batch(teacher_count)
        students = []
        
        for i in range(student_count):
            # Assign students to teachers round-robin
            assigned_teacher = teachers[i % len(teachers)]
            student = StudentFactory.create(assigned_teacher=assigned_teacher)
            students.append(student)
        
        return {
            'teachers': teachers,
            'students': students,
            'admin': AdminUserFactory.create()
        }


class SchoolSetupFactory:
    """Factory for creating a complete school setup"""
    
    @staticmethod
    def create_school():
        """Create a complete school with multiple classrooms"""
        setup = {
            'admin_users': AdminUserFactory.create_batch(2),
            'teachers': [],
            'students': [],
            'classrooms': []
        }
        
        # Create teachers for different subjects
        subjects = ['Mathematics', 'Science', 'English', 'History']
        for subject in subjects:
            teachers = TeacherFactory.create_batch(2, subject_specialization=subject)
            setup['teachers'].extend(teachers)
        
        # Create students for different grades
        grades = ['6', '7', '8', '9', '10', '11', '12']
        for grade in grades:
            students = StudentFactory.create_batch(15, class_grade=grade)
            setup['students'].extend(students)
        
        return setup


# Data validation factories
class InvalidDataFactory:
    """Factory for creating invalid data for testing validation"""
    
    @staticmethod
    def invalid_user_data():
        return {
            'username': '',  # Empty username
            'email': 'invalid-email',  # Invalid email format
            'password': '123',  # Too short password
            'first_name': 'A' * 151,  # Too long first name
        }
    
    @staticmethod
    def invalid_student_data():
        return {
            'first_name': '',  # Empty first name
            'last_name': '',  # Empty last name
            'email': 'invalid-email',  # Invalid email
            'phone_number': '123',  # Too short phone number
            'roll_number': '',  # Empty roll number
            'class_grade': '15',  # Invalid grade
            'date_of_birth': '2030-01-01',  # Future date
            'admission_date': '1990-01-01',  # Too old date
        }
    
    @staticmethod
    def invalid_teacher_data():
        return {
            'first_name': '',  # Empty first name
            'last_name': '',  # Empty last name
            'email': 'invalid-email',  # Invalid email
            'phone_number': '123',  # Too short phone number
            'subject_specialization': '',  # Empty subject
            'employee_id': '',  # Empty employee ID
            'date_of_joining': '2030-01-01',  # Future date
        }


# Performance test factories
class PerformanceTestFactory:
    """Factory for creating large datasets for performance testing"""
    
    @staticmethod
    def create_large_dataset(student_count=1000, teacher_count=50):
        """Create a large dataset for performance testing"""
        print(f"Creating {teacher_count} teachers...")
        teachers = TeacherFactory.create_batch(teacher_count)
        
        print(f"Creating {student_count} students...")
        students = []
        for i in range(student_count):
            if i % 100 == 0:
                print(f"Created {i} students...")
            
            # Assign students to teachers
            assigned_teacher = teachers[i % len(teachers)]
            student = StudentFactory.create(assigned_teacher=assigned_teacher)
            students.append(student)
        
        print("Large dataset creation complete!")
        return {
            'teachers': teachers,
            'students': students,
            'total_users': len(teachers) + len(students)
        }