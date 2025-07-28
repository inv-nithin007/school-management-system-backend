"""
Core functionality tests for Teachers app
Import only essential, stable tests
"""
from tests.test_core_functionality import CoreTeacherModelTest
from tests.test_core_serializers import CoreTeacherSerializerTest
from tests.test_core_views import CoreTeacherViewTest

# Re-export for Django test discovery
__all__ = [
    'CoreTeacherModelTest',
    'CoreTeacherSerializerTest', 
    'CoreTeacherViewTest',
]