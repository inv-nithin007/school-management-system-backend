"""
Core functionality tests for Accounts app
Import only essential, stable tests
"""
from tests.test_core_functionality import CoreUserProfileTest
from tests.test_core_views import CorePermissionTest

# Re-export for Django test discovery
__all__ = [
    'CoreUserProfileTest',
    'CorePermissionTest',
]