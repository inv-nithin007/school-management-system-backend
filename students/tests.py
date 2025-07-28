"""
Core functionality tests for Students app
Import only essential, stable tests
"""
from tests.test_core_functionality import CoreStudentModelTest
from tests.test_core_serializers import CoreStudentSerializerTest
from tests.test_core_views import CoreStudentViewTest

# Re-export for Django test discovery
__all__ = [
    'CoreStudentModelTest',
    'CoreStudentSerializerTest', 
    'CoreStudentViewTest',
]