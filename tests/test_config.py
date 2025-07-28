"""
Test configuration and settings
"""
import os
import sys
from django.conf import settings

# Test database configuration
TEST_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Test cache configuration
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Test logging configuration
TEST_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'tests/test.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'tests': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Test email backend
TEST_EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Test media settings
TEST_MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_media')
TEST_MEDIA_URL = '/test_media/'

# Test static settings
TEST_STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_static')
TEST_STATIC_URL = '/test_static/'

# Test security settings
TEST_SECRET_KEY = 'test-secret-key-for-testing-only'
TEST_DEBUG = True
TEST_ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Test middleware (minimal for testing)
TEST_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Test REST framework settings
TEST_REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Test performance settings
TEST_PERFORMANCE_THRESHOLDS = {
    'api_response_time': 2.0,  # seconds
    'database_query_time': 0.5,  # seconds
    'bulk_operation_time': 5.0,  # seconds
    'csv_export_time': 10.0,  # seconds
}

# Test concurrency settings
TEST_CONCURRENCY = {
    'max_threads': 10,
    'max_concurrent_requests': 20,
    'timeout': 30,  # seconds
}

# Test data size limits
TEST_DATA_LIMITS = {
    'max_students_for_unit_tests': 100,
    'max_students_for_integration_tests': 500,
    'max_students_for_performance_tests': 1000,
    'max_teachers_for_unit_tests': 20,
    'max_teachers_for_integration_tests': 50,
    'max_teachers_for_performance_tests': 100,
}

# Test coverage settings
TEST_COVERAGE_CONFIG = {
    'minimum_coverage': 80,
    'fail_under': 80,
    'show_missing': True,
    'skip_covered': False,
}

# Test factory settings
TEST_FACTORY_SETTINGS = {
    'use_sequence_numbers': True,
    'reset_sequences': True,
    'cleanup_files': True,
}

# Test environment variables
TEST_ENV_VARS = {
    'DJANGO_SETTINGS_MODULE': 'school_management.settings',
    'TESTING': 'True',
    'DEBUG': 'False',
    'USE_TZ': 'True',
}

# Test database connection settings
TEST_DATABASE_SETTINGS = {
    'CONN_MAX_AGE': 0,  # Don't persist connections
    'CONN_HEALTH_CHECKS': False,
    'AUTOCOMMIT': True,
}

# Test security settings
TEST_SECURITY_SETTINGS = {
    'SECURE_SSL_REDIRECT': False,
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'X_FRAME_OPTIONS': 'DENY',
    'CSRF_COOKIE_SECURE': False,  # For testing
    'SESSION_COOKIE_SECURE': False,  # For testing
}

# Test file upload settings
TEST_FILE_UPLOAD_SETTINGS = {
    'FILE_UPLOAD_MAX_MEMORY_SIZE': 2621440,  # 2.5MB
    'DATA_UPLOAD_MAX_MEMORY_SIZE': 2621440,  # 2.5MB
    'FILE_UPLOAD_TEMP_DIR': None,
    'FILE_UPLOAD_PERMISSIONS': 0o644,
}

# Test timezone settings
TEST_TIMEZONE_SETTINGS = {
    'TIME_ZONE': 'UTC',
    'USE_TZ': True,
    'USE_I18N': True,
    'USE_L10N': True,
}

# Test session settings
TEST_SESSION_SETTINGS = {
    'SESSION_ENGINE': 'django.contrib.sessions.backends.db',
    'SESSION_COOKIE_AGE': 1209600,  # 2 weeks
    'SESSION_SAVE_EVERY_REQUEST': False,
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': False,
}

# Test password validation (minimal for testing)
TEST_AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,  # Reduced for testing
        }
    },
]

# Test JWT settings
TEST_JWT_SETTINGS = {
    'ACCESS_TOKEN_LIFETIME': 60 * 60,  # 1 hour
    'REFRESH_TOKEN_LIFETIME': 24 * 60 * 60,  # 24 hours
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': TEST_SECRET_KEY,
}

# Test fixture settings
TEST_FIXTURES = [
    'tests/fixtures/test_users.json',
    'tests/fixtures/test_students.json',
    'tests/fixtures/test_teachers.json',
]

# Test cleanup settings
TEST_CLEANUP = {
    'cleanup_files': True,
    'cleanup_database': True,
    'cleanup_cache': True,
    'cleanup_sessions': True,
}

# Test reporting settings
TEST_REPORTING = {
    'generate_html_report': True,
    'generate_xml_report': True,
    'generate_json_report': True,
    'report_directory': 'tests/reports',
}

# Test parallel execution settings
TEST_PARALLEL = {
    'enable_parallel': True,
    'max_processes': 4,
    'test_discovery_timeout': 30,
}

# Test mock settings
TEST_MOCK_SETTINGS = {
    'mock_external_apis': True,
    'mock_email_backend': True,
    'mock_file_storage': True,
    'mock_third_party_services': True,
}

# Test monitoring settings
TEST_MONITORING = {
    'enable_performance_monitoring': True,
    'enable_memory_monitoring': True,
    'enable_database_monitoring': True,
    'monitoring_interval': 1.0,  # seconds
}

# Test retry settings
TEST_RETRY = {
    'enable_retry': True,
    'max_retries': 3,
    'retry_delay': 1.0,  # seconds
    'retry_backoff': 2.0,  # multiplier
}

# Test timeout settings
TEST_TIMEOUTS = {
    'default_timeout': 30,  # seconds
    'slow_test_timeout': 60,  # seconds
    'integration_test_timeout': 120,  # seconds
    'performance_test_timeout': 300,  # seconds
}


class TestConfiguration:
    """Central configuration class for tests"""
    
    def __init__(self):
        self.databases = TEST_DATABASES
        self.caches = TEST_CACHES
        self.logging = TEST_LOGGING
        self.performance_thresholds = TEST_PERFORMANCE_THRESHOLDS
        self.concurrency = TEST_CONCURRENCY
        self.data_limits = TEST_DATA_LIMITS
        self.coverage = TEST_COVERAGE_CONFIG
        self.factory_settings = TEST_FACTORY_SETTINGS
        self.cleanup = TEST_CLEANUP
        self.reporting = TEST_REPORTING
        self.parallel = TEST_PARALLEL
        self.mock_settings = TEST_MOCK_SETTINGS
        self.monitoring = TEST_MONITORING
        self.retry = TEST_RETRY
        self.timeouts = TEST_TIMEOUTS
    
    def get_database_config(self):
        """Get database configuration for tests"""
        return self.databases
    
    def get_performance_threshold(self, operation):
        """Get performance threshold for specific operation"""
        return self.performance_thresholds.get(operation, 5.0)
    
    def get_data_limit(self, model, test_type):
        """Get data limit for specific model and test type"""
        key = f'max_{model}_for_{test_type}_tests'
        return self.data_limits.get(key, 100)
    
    def should_cleanup(self, resource):
        """Check if resource should be cleaned up"""
        key = f'cleanup_{resource}'
        return self.cleanup.get(key, True)
    
    def get_timeout(self, test_type):
        """Get timeout for specific test type"""
        key = f'{test_type}_timeout'
        return self.timeouts.get(key, self.timeouts['default_timeout'])
    
    def should_mock(self, service):
        """Check if service should be mocked"""
        key = f'mock_{service}'
        return self.mock_settings.get(key, False)
    
    def get_concurrency_limit(self, resource):
        """Get concurrency limit for specific resource"""
        key = f'max_{resource}'
        return self.concurrency.get(key, 10)


# Global test configuration instance
test_config = TestConfiguration()


def configure_test_environment():
    """Configure Django settings for testing"""
    if not settings.configured:
        settings.configure(
            DEBUG=TEST_DEBUG,
            DATABASES=TEST_DATABASES,
            CACHES=TEST_CACHES,
            LOGGING=TEST_LOGGING,
            EMAIL_BACKEND=TEST_EMAIL_BACKEND,
            MEDIA_ROOT=TEST_MEDIA_ROOT,
            MEDIA_URL=TEST_MEDIA_URL,
            STATIC_ROOT=TEST_STATIC_ROOT,
            STATIC_URL=TEST_STATIC_URL,
            SECRET_KEY=TEST_SECRET_KEY,
            ALLOWED_HOSTS=TEST_ALLOWED_HOSTS,
            MIDDLEWARE=TEST_MIDDLEWARE,
            REST_FRAMEWORK=TEST_REST_FRAMEWORK,
            AUTH_PASSWORD_VALIDATORS=TEST_AUTH_PASSWORD_VALIDATORS,
            TIME_ZONE=TEST_TIMEZONE_SETTINGS['TIME_ZONE'],
            USE_TZ=TEST_TIMEZONE_SETTINGS['USE_TZ'],
            USE_I18N=TEST_TIMEZONE_SETTINGS['USE_I18N'],
            USE_L10N=TEST_TIMEZONE_SETTINGS['USE_L10N'],
            SESSION_ENGINE=TEST_SESSION_SETTINGS['SESSION_ENGINE'],
            SESSION_COOKIE_AGE=TEST_SESSION_SETTINGS['SESSION_COOKIE_AGE'],
            **TEST_SECURITY_SETTINGS,
            **TEST_FILE_UPLOAD_SETTINGS,
        )
    
    # Set environment variables
    for key, value in TEST_ENV_VARS.items():
        os.environ.setdefault(key, value)


def setup_test_directories():
    """Set up test directories"""
    directories = [
        TEST_MEDIA_ROOT,
        TEST_STATIC_ROOT,
        'tests/reports',
        'tests/fixtures',
        'tests/logs',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def cleanup_test_environment():
    """Clean up test environment"""
    import shutil
    
    if test_config.should_cleanup('files'):
        # Clean up test files
        cleanup_directories = [
            TEST_MEDIA_ROOT,
            TEST_STATIC_ROOT,
            'tests/reports',
            'tests/logs',
        ]
        
        for directory in cleanup_directories:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)
    
    if test_config.should_cleanup('cache'):
        # Clear cache
        from django.core.cache import cache
        cache.clear()


# Test markers for pytest
TEST_MARKERS = {
    'unit': 'Unit tests',
    'integration': 'Integration tests',
    'performance': 'Performance tests',
    'slow': 'Slow tests',
    'concurrent': 'Concurrent tests',
    'database': 'Database tests',
    'api': 'API tests',
    'security': 'Security tests',
    'load': 'Load tests',
    'stress': 'Stress tests',
}

# Test categories
TEST_CATEGORIES = {
    'models': 'Model tests',
    'views': 'View tests',
    'serializers': 'Serializer tests',
    'permissions': 'Permission tests',
    'authentication': 'Authentication tests',
    'validation': 'Validation tests',
    'export': 'Export functionality tests',
    'import': 'Import functionality tests',
}

# Test priority levels
TEST_PRIORITIES = {
    'critical': 'Critical tests that must pass',
    'high': 'High priority tests',
    'medium': 'Medium priority tests',
    'low': 'Low priority tests',
}

# Test execution order
TEST_EXECUTION_ORDER = [
    'unit',
    'integration',
    'performance',
    'security',
    'load',
    'stress',
]

# Test dependencies
TEST_DEPENDENCIES = {
    'integration': ['unit'],
    'performance': ['unit', 'integration'],
    'load': ['unit', 'integration', 'performance'],
    'stress': ['unit', 'integration', 'performance', 'load'],
}
