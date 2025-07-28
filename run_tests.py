#!/usr/bin/env python
"""
Industrial-level test runner for the School Management System
"""
import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command
from tests.test_config import test_config, setup_test_directories, cleanup_test_environment


class TestRunner:
    """Industrial-level test runner with comprehensive features"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.failed_tests = []
        self.setup_environment()
    
    def setup_environment(self):
        """Set up test environment"""
        print("Setting up test environment...")
        setup_test_directories()
        
        # Install test requirements if needed
        self.install_test_requirements()
        
        # Run initial migrations
        self.run_migrations()
    
    def install_test_requirements(self):
        """Install test requirements"""
        requirements_file = project_root / 'test_requirements.txt'
        if requirements_file.exists():
            print("Installing test requirements...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True, capture_output=True)
    
    def run_migrations(self):
        """Run database migrations"""
        print("Running database migrations...")
        call_command('migrate', verbosity=0, interactive=False)
    
    def run_unit_tests(self, pattern=None, verbosity=2):
        """Run unit tests"""
        print("\n" + "="*60)
        print("RUNNING UNIT TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_student_models',
            'tests.test_student_serializers',
            'accounts.tests',
            'students.tests',
            'teachers.tests',
        ]
        
        if pattern:
            test_labels = [label for label in test_labels if pattern in label]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_integration_tests(self, pattern=None, verbosity=2):
        """Run integration tests"""
        print("\n" + "="*60)
        print("RUNNING INTEGRATION TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_integration.SchoolManagementIntegrationTest',
            'tests.test_integration.SecurityIntegrationTest',
            'tests.test_integration.CacheIntegrationTest',
            'tests.test_integration.DataIntegrityTest',
        ]
        
        if pattern:
            test_labels = [label for label in test_labels if pattern in label]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_performance_tests(self, pattern=None, verbosity=2):
        """Run performance tests"""
        print("\n" + "="*60)
        print("RUNNING PERFORMANCE TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_integration.PerformanceTestSuite',
            'tests.test_integration.LoadTestSuite',
            'tests.test_student_models.StudentModelPerformanceTest',
        ]
        
        if pattern:
            test_labels = [label for label in test_labels if pattern in label]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_view_tests(self, pattern=None, verbosity=2):
        """Run view tests"""
        print("\n" + "="*60)
        print("RUNNING VIEW TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_student_views',
        ]
        
        if pattern:
            test_labels = [label for label in test_labels if pattern in label]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_all_tests(self, verbosity=2):
        """Run all tests"""
        print("\n" + "="*60)
        print("RUNNING ALL TESTS")
        print("="*60)
        
        test_labels = [
            'tests',
            'accounts.tests',
            'students.tests',
            'teachers.tests',
            'school_management.tests',
        ]
        
        return self._run_tests(test_labels, verbosity)
    
    def _run_tests(self, test_labels, verbosity=2):
        """Run specific test labels"""
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=verbosity)
        
        start_time = time.time()
        failures = test_runner.run_tests(test_labels)
        end_time = time.time()
        
        duration = end_time - start_time
        
        result = {
            'test_labels': test_labels,
            'failures': failures,
            'duration': duration,
            'success': failures == 0
        }
        
        self.results[str(test_labels)] = result
        
        if failures > 0:
            self.failed_tests.extend(test_labels)
        
        print(f"\nTest Duration: {duration:.2f} seconds")
        print(f"Test Result: {'PASS' if failures == 0 else 'FAIL'}")
        
        return result
    
    def run_coverage_tests(self, verbosity=2):
        """Run tests with coverage analysis"""
        print("\n" + "="*60)
        print("RUNNING COVERAGE ANALYSIS")
        print("="*60)
        
        # Install coverage if not available
        try:
            import coverage
        except ImportError:
            print("Installing coverage...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'], check=True)
            import coverage
        
        # Start coverage
        cov = coverage.Coverage(source=['.'], omit=[
            'venv/*',
            'tests/*',
            'manage.py',
            '*/migrations/*',
            '*/settings.py',
            '*/venv/*',
            '*/virtualenv/*',
        ])
        
        cov.start()
        
        # Run tests
        result = self.run_all_tests(verbosity)
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Generate reports
        print("\nGenerating coverage reports...")
        
        # Console report
        print("\nCoverage Report:")
        cov.report(show_missing=True)
        
        # HTML report
        html_dir = project_root / 'htmlcov'
        cov.html_report(directory=str(html_dir))
        print(f"HTML coverage report generated in {html_dir}")
        
        # XML report
        xml_file = project_root / 'coverage.xml'
        cov.xml_report(outfile=str(xml_file))
        print(f"XML coverage report generated: {xml_file}")
        
        # Check coverage threshold
        total_coverage = cov.report(show_missing=False)
        threshold = test_config.coverage['minimum_coverage']
        
        if total_coverage < threshold:
            print(f"\nWARNING: Coverage {total_coverage:.1f}% is below threshold {threshold}%")
            result['coverage_warning'] = True
        else:
            print(f"\nCoverage {total_coverage:.1f}% meets threshold {threshold}%")
        
        result['coverage'] = total_coverage
        return result
    
    def run_security_tests(self, verbosity=2):
        """Run security tests"""
        print("\n" + "="*60)
        print("RUNNING SECURITY TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_integration.SecurityIntegrationTest',
        ]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_load_tests(self, verbosity=2):
        """Run load tests"""
        print("\n" + "="*60)
        print("RUNNING LOAD TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_integration.LoadTestSuite',
        ]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_concurrent_tests(self, verbosity=2):
        """Run concurrent tests"""
        print("\n" + "="*60)
        print("RUNNING CONCURRENT TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_student_models.StudentModelConcurrencyTest',
        ]
        
        return self._run_tests(test_labels, verbosity)
    
    def run_database_tests(self, verbosity=2):
        """Run database tests"""
        print("\n" + "="*60)
        print("RUNNING DATABASE TESTS")
        print("="*60)
        
        test_labels = [
            'tests.test_student_models.StudentModelTransactionTest',
            'tests.test_integration.DataIntegrityTest',
        ]
        
        return self._run_tests(test_labels, verbosity)
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("GENERATING TEST REPORT")
        print("="*60)
        
        total_duration = sum(result['duration'] for result in self.results.values())
        total_failures = sum(result['failures'] for result in self.results.values())
        total_tests = len(self.results)
        
        report = f"""
TEST EXECUTION REPORT
====================
Total Test Suites: {total_tests}
Total Duration: {total_duration:.2f} seconds
Total Failures: {total_failures}
Overall Status: {'PASS' if total_failures == 0 else 'FAIL'}

DETAILED RESULTS:
"""
        
        for test_label, result in self.results.items():
            status = 'PASS' if result['success'] else 'FAIL'
            report += f"""
- {test_label}
  Status: {status}
  Duration: {result['duration']:.2f}s
  Failures: {result['failures']}
"""
        
        if self.failed_tests:
            report += f"""
FAILED TESTS:
{chr(10).join(self.failed_tests)}
"""
        
        report += f"""
RECOMMENDATIONS:
"""
        
        if total_failures > 0:
            report += "- Fix failing tests before deployment\n"
        
        if total_duration > 60:
            report += "- Consider optimizing slow tests\n"
        
        if 'coverage' in self.results:
            coverage = self.results.get('coverage', {}).get('coverage', 0)
            if coverage < 90:
                report += f"- Improve test coverage (current: {coverage:.1f}%)\n"
        
        report += "- Run tests in CI/CD pipeline\n"
        report += "- Monitor test performance over time\n"
        
        print(report)
        
        # Save report to file
        report_file = project_root / 'test_report.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Test report saved to {report_file}")
    
    def cleanup(self):
        """Clean up test environment"""
        print("\nCleaning up test environment...")
        cleanup_test_environment()
        print("Cleanup complete.")
    
    def run(self, test_type='all', pattern=None, verbosity=2, coverage=False):
        """Run tests based on type"""
        self.start_time = time.time()
        
        try:
            if test_type == 'unit':
                result = self.run_unit_tests(pattern, verbosity)
            elif test_type == 'integration':
                result = self.run_integration_tests(pattern, verbosity)
            elif test_type == 'performance':
                result = self.run_performance_tests(pattern, verbosity)
            elif test_type == 'views':
                result = self.run_view_tests(pattern, verbosity)
            elif test_type == 'security':
                result = self.run_security_tests(verbosity)
            elif test_type == 'load':
                result = self.run_load_tests(verbosity)
            elif test_type == 'concurrent':
                result = self.run_concurrent_tests(verbosity)
            elif test_type == 'database':
                result = self.run_database_tests(verbosity)
            elif test_type == 'coverage':
                result = self.run_coverage_tests(verbosity)
            elif test_type == 'all':
                if coverage:
                    result = self.run_coverage_tests(verbosity)
                else:
                    result = self.run_all_tests(verbosity)
            else:
                print(f"Unknown test type: {test_type}")
                return False
            
            self.end_time = time.time()
            
            # Generate report
            self.generate_test_report()
            
            return result.get('success', False)
        
        except Exception as e:
            print(f"Error running tests: {e}")
            return False
        
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Industrial-level test runner')
    parser.add_argument('test_type', nargs='?', default='all',
                       choices=['all', 'unit', 'integration', 'performance', 'views', 
                               'security', 'load', 'concurrent', 'database', 'coverage'],
                       help='Type of tests to run')
    parser.add_argument('--pattern', '-p', help='Pattern to filter tests')
    parser.add_argument('--verbosity', '-v', type=int, default=2, choices=[0, 1, 2, 3],
                       help='Verbosity level')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage analysis')
    parser.add_argument('--failfast', '-f', action='store_true',
                       help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Configure Django settings for failfast
    if args.failfast:
        os.environ['DJANGO_TEST_FAILFAST'] = '1'
    
    runner = TestRunner()
    
    print("Industrial-Level Test Runner")
    print("="*60)
    print(f"Test Type: {args.test_type}")
    print(f"Pattern: {args.pattern or 'None'}")
    print(f"Verbosity: {args.verbosity}")
    print(f"Coverage: {args.coverage}")
    print(f"Fail Fast: {args.failfast}")
    print("="*60)
    
    success = runner.run(
        test_type=args.test_type,
        pattern=args.pattern,
        verbosity=args.verbosity,
        coverage=args.coverage
    )
    
    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()