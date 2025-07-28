"""
Core functionality tests for School Management
Import only essential, stable tests
"""
from tests.test_core_functionality import CoreDatabaseOperationsTest
from tests.test_core_views import CoreCSVExportTest

# Re-export for Django test discovery
__all__ = [
    'CoreDatabaseOperationsTest',
    'CoreCSVExportTest',
]