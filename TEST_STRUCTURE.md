# Unit Test Structure - Simple & Hardcoded Tests

## Test Files Created

I've created separate test files for models, views, and serializers with simple hardcoded tests as requested:

### Accounts App Tests
- `accounts/model_tests.py` - Tests for UserProfile and PasswordResetToken models
- `accounts/view_tests.py` - Tests for login, register, forgot password, and reset password views

### Students App Tests  
- `students/model_tests.py` - Tests for Student model
- `students/view_tests.py` - Tests for Student CRUD operations and CSV import
- `students/serializer_tests.py` - Tests for Student serializer validation

### Teachers App Tests
- `teachers/model_tests.py` - Tests for Teacher model
- `teachers/view_tests.py` - Tests for Teacher CRUD operations
- `teachers/serializer_tests.py` - Tests for Teacher serializer validation

### Exams App Tests
- `exams/model_tests.py` - Tests for Exam, Question, StudentExam, and StudentAnswer models
- `exams/view_tests.py` - Tests for exam creation, taking, and submission
- `exams/serializer_tests.py` - Tests for exam-related serializers

## Test Characteristics

### ✅ Simple & Beginner-Friendly
- All tests use hardcoded data (no factories like FactoryBoy)
- Clear test method names like `test_create_student()`, `test_login_success()`
- Basic assertions using `assertEqual()`, `assertTrue()`, `assertFalse()`
- Simple test data setup in `setUp()` methods

### ✅ Hardcoded Test Data Examples
```python
def test_create_student(self):
    student = Student.objects.create(
        user=self.user,
        first_name='John',
        last_name='Doe',
        email='student@example.com',
        phone_number='9876543210',
        roll_number='STU001',
        class_grade='10',
        date_of_birth='2005-01-01',
        admission_date='2020-04-01'
    )
    
    self.assertEqual(student.first_name, 'John')
    self.assertEqual(student.last_name, 'Doe')
```

### ✅ Simple Coverage Areas
- **Model Tests**: Basic CRUD operations, field validation, string representations
- **View Tests**: HTTP status codes, authentication, permissions, API responses
- **Serializer Tests**: Data validation, error handling, field requirements

### ✅ No Advanced Testing Features
- No mocking or complex test fixtures
- No parametrized tests
- No test inheritance hierarchies
- No complex test utilities
- No automated test data generation

## Running Tests

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test Files
```bash
python manage.py test accounts.model_tests
python manage.py test students.serializer_tests
python manage.py test teachers.view_tests
python manage.py test exams.model_tests
```

### Run Tests with Coverage
```bash
python manage.py test --verbosity=2
```

## Test Coverage

The tests cover:
- ✅ All model fields and methods
- ✅ All API endpoints (GET, POST, PUT, DELETE)
- ✅ All serializer validations
- ✅ Authentication and permissions
- ✅ CSV import functionality
- ✅ Password reset workflow
- ✅ Exam taking and grading
- ✅ Error handling scenarios

## Simple Test Examples

### Model Test
```python
def test_user_profile_default_role(self):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    profile = UserProfile.objects.create(user=user)
    
    self.assertEqual(profile.role, 'student')
```

### View Test
```python
def test_login_success(self):
    url = reverse('login')
    data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = self.client.post(url, data, format='json')
    
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIn('access', response.data)
```

### Serializer Test
```python
def test_student_serializer_invalid_email(self):
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'invalid-email',
        'phone_number': '9876543210',
        'roll_number': 'STU001',
        'class_grade': '10',
        'date_of_birth': '2005-01-01',
        'admission_date': '2020-04-01'
    }
    
    serializer = StudentSerializer(data=data)
    self.assertFalse(serializer.is_valid())
    self.assertIn('email', serializer.errors)
```

This test structure provides comprehensive coverage while maintaining simplicity suitable for Django beginners.