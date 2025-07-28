"""
Comprehensive test suite for Accounts models with database transactions and edge cases
"""
from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
import threading
import time

from .utils import BaseTestCase, DatabaseMixin, ConcurrencyTestMixin
from .factories import UserFactory, AdminUserFactory, UserProfileFactory
from accounts.models import UserProfile


class UserProfileModelTest(BaseTestCase, DatabaseMixin):
    """Test suite for UserProfile model basic functionality"""
    
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
    
    def test_user_profile_creation(self):
        """Test basic user profile creation"""
        profile = UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        self.assertIsNotNone(profile.id)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.role, 'student')
    
    def test_user_profile_str_representation(self):
        """Test user profile string representation"""
        profile = UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        expected_str = f'{self.user.username} - student'
        self.assertEqual(str(profile), expected_str)
    
    def test_user_profile_role_choices(self):
        """Test user profile role choices"""
        valid_roles = ['admin', 'teacher', 'student']
        
        for role in valid_roles:
            profile = UserProfile.objects.create(
                user=UserFactory(),
                role=role
            )
            self.assertEqual(profile.role, role)
            self.assertIn(profile.role, valid_roles)
    
    def test_user_profile_invalid_role(self):
        """Test user profile with invalid role"""
        with self.assertRaises(ValidationError):
            profile = UserProfile(
                user=self.user,
                role='invalid_role'
            )
            profile.full_clean()
    
    def test_user_profile_unique_constraint(self):
        """Test user profile unique constraint"""
        # Create first profile
        UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        # Try to create another profile for same user
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(
                user=self.user,
                role='teacher'
            )
    
    def test_user_profile_cascade_deletion(self):
        """Test user profile cascade deletion"""
        profile = UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        profile_id = profile.id
        user_id = self.user.id
        
        # Delete user
        self.user.delete()
        
        # Profile should also be deleted
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())
        self.assertFalse(User.objects.filter(id=user_id).exists())
    
    def test_user_profile_factory(self):
        """Test user profile factory"""
        profile = UserProfileFactory()
        
        self.assertIsNotNone(profile.id)
        self.assertIsNotNone(profile.user)
        self.assertIn(profile.role, ['admin', 'teacher', 'student'])
    
    def test_user_profile_with_admin_user(self):
        """Test user profile with admin user"""
        admin_user = AdminUserFactory()
        profile = UserProfile.objects.create(
            user=admin_user,
            role='admin'
        )
        
        self.assertEqual(profile.role, 'admin')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
    
    def test_user_profile_timestamps(self):
        """Test user profile timestamps"""
        profile = UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        # Check timestamps exist
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        
        # Check timestamps are recent
        import datetime
        now = datetime.datetime.now()
        self.assertLess(abs((now - profile.created_at.replace(tzinfo=None)).total_seconds()), 60)
    
    def test_user_profile_update_timestamps(self):
        """Test user profile update timestamps"""
        profile = UserProfile.objects.create(
            user=self.user,
            role='student'
        )
        
        original_updated_at = profile.updated_at
        
        # Wait a bit and update
        time.sleep(0.1)
        profile.role = 'teacher'
        profile.save()
        
        # Updated timestamp should change
        self.assertNotEqual(profile.updated_at, original_updated_at)
    
    def test_user_profile_related_queries(self):
        """Test user profile related queries"""
        # Create profiles with different roles
        student_users = [UserFactory() for _ in range(3)]
        teacher_users = [UserFactory() for _ in range(2)]
        admin_users = [AdminUserFactory() for _ in range(1)]
        
        for user in student_users:
            UserProfile.objects.create(user=user, role='student')
        
        for user in teacher_users:
            UserProfile.objects.create(user=user, role='teacher')
        
        for user in admin_users:
            UserProfile.objects.create(user=user, role='admin')
        
        # Test filtering by role
        student_profiles = UserProfile.objects.filter(role='student')
        teacher_profiles = UserProfile.objects.filter(role='teacher')
        admin_profiles = UserProfile.objects.filter(role='admin')
        
        self.assertEqual(student_profiles.count(), 3)
        self.assertEqual(teacher_profiles.count(), 2)
        self.assertEqual(admin_profiles.count(), 1)
    
    def test_user_profile_select_related(self):
        """Test user profile select_related performance"""
        profiles = []
        for i in range(10):
            user = UserFactory()
            profile = UserProfile.objects.create(user=user, role='student')
            profiles.append(profile)
        
        # Test select_related
        with self.assertNumQueries(1):
            profiles_with_users = UserProfile.objects.select_related('user').all()
            for profile in profiles_with_users:
                # Access user field - should not trigger additional queries
                username = profile.user.username


class UserProfileModelTransactionTest(TransactionTestCase):
    """Test suite for UserProfile model database transactions"""
    
    def test_user_profile_creation_in_transaction(self):
        """Test user profile creation within transaction"""
        initial_count = UserProfile.objects.count()
        
        with transaction.atomic():
            user = UserFactory()
            profile = UserProfile.objects.create(user=user, role='student')
            self.assertIsNotNone(profile.id)
            
            # Count should increase within transaction
            self.assertEqual(UserProfile.objects.count(), initial_count + 1)
        
        # Count should remain after transaction
        self.assertEqual(UserProfile.objects.count(), initial_count + 1)
    
    def test_user_profile_creation_transaction_rollback(self):
        """Test user profile creation transaction rollback"""
        initial_count = UserProfile.objects.count()
        
        try:
            with transaction.atomic():
                user = UserFactory()
                profile = UserProfile.objects.create(user=user, role='student')
                self.assertIsNotNone(profile.id)
                
                # Force rollback
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Count should remain unchanged after rollback
        self.assertEqual(UserProfile.objects.count(), initial_count)
    
    def test_user_profile_update_in_transaction(self):
        """Test user profile update within transaction"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        
        with transaction.atomic():
            profile.role = 'teacher'
            profile.save()
            
            # Should be updated within transaction
            updated_profile = UserProfile.objects.get(id=profile.id)
            self.assertEqual(updated_profile.role, 'teacher')
        
        # Should remain updated after transaction
        final_profile = UserProfile.objects.get(id=profile.id)
        self.assertEqual(final_profile.role, 'teacher')
    
    def test_user_profile_update_transaction_rollback(self):
        """Test user profile update transaction rollback"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        original_role = profile.role
        
        try:
            with transaction.atomic():
                profile.role = 'teacher'
                profile.save()
                
                # Force rollback
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Should revert to original after rollback
        reverted_profile = UserProfile.objects.get(id=profile.id)
        self.assertEqual(reverted_profile.role, original_role)
    
    def test_user_profile_integrity_constraint_in_transaction(self):
        """Test integrity constraint violation in transaction"""
        user = UserFactory()
        profile1 = UserProfile.objects.create(user=user, role='student')
        initial_count = UserProfile.objects.count()
        
        try:
            with transaction.atomic():
                # This should fail due to unique constraint
                profile2 = UserProfile.objects.create(user=user, role='teacher')
        except IntegrityError:
            pass
        
        # Count should remain unchanged
        self.assertEqual(UserProfile.objects.count(), initial_count)


class UserProfileModelConcurrencyTest(TransactionTestCase, ConcurrencyTestMixin):
    """Test suite for UserProfile model concurrency scenarios"""
    
    def test_concurrent_user_profile_creation(self):
        """Test concurrent user profile creation"""
        def create_user_profile():
            try:
                user = UserFactory()
                profile = UserProfile.objects.create(
                    user=user,
                    role='student'
                )
                return profile
            except Exception as e:
                return e
        
        # Test concurrent creation
        results, errors = self.test_concurrent_access(create_user_profile, num_threads=5)
        
        # Should handle concurrent creation
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
        
        # All profiles should be created
        for result in results:
            self.assertIsInstance(result, UserProfile)
    
    def test_concurrent_user_profile_update(self):
        """Test concurrent user profile update"""
        user = UserFactory()
        profile = UserProfile.objects.create(user=user, role='student')
        
        def update_user_profile():
            try:
                p = UserProfile.objects.get(id=profile.id)
                p.role = 'teacher'
                p.save()
                return p
            except Exception as e:
                return e
        
        # Test concurrent updates
        results, errors = self.test_concurrent_access(update_user_profile, num_threads=3)
        
        # Should handle concurrent updates
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 3)
        
        # Final state should be consistent
        final_profile = UserProfile.objects.get(id=profile.id)
        self.assertEqual(final_profile.role, 'teacher')
    
    def test_race_condition_prevention(self):
        """Test race condition prevention in unique constraints"""
        user = UserFactory()
        
        def create_duplicate_profile():
            try:
                profile = UserProfile.objects.create(
                    user=user,
                    role='student'
                )
                return profile
            except IntegrityError:
                return 'IntegrityError'
            except Exception as e:
                return e
        
        # Test concurrent creation for same user
        results, errors = self.test_concurrent_access(create_duplicate_profile, num_threads=3)
        
        # Should have exactly one success and multiple integrity errors
        profiles = [r for r in results if isinstance(r, UserProfile)]
        integrity_errors = [r for r in results if r == 'IntegrityError']
        
        self.assertEqual(len(profiles), 1)
        self.assertEqual(len(integrity_errors), 2)


class UserProfileModelEdgeCasesTest(BaseTestCase):
    """Test edge cases for UserProfile model"""
    
    def test_user_profile_with_unicode_username(self):
        """Test user profile with Unicode username"""
        user = UserFactory(username='josé_garcía')
        profile = UserProfile.objects.create(user=user, role='student')
        
        # Should handle Unicode properly
        self.assertEqual(profile.user.username, 'josé_garcía')
        self.assertEqual(str(profile), 'josé_garcía - student')
    
    def test_user_profile_with_special_characters(self):
        """Test user profile with special characters in username"""
        user = UserFactory(username="o'connor.smith")
        profile = UserProfile.objects.create(user=user, role='teacher')
        
        # Should handle special characters
        self.assertEqual(profile.user.username, "o'connor.smith")
        self.assertEqual(str(profile), "o'connor.smith - teacher")
    
    def test_user_profile_with_very_long_username(self):
        """Test user profile with very long username"""
        long_username = 'a' * 150  # Django default is 150 chars
        user = UserFactory(username=long_username)
        profile = UserProfile.objects.create(user=user, role='admin')
        
        self.assertEqual(profile.user.username, long_username)
        self.assertEqual(len(profile.user.username), 150)
    
    def test_user_profile_managers(self):
        """Test user profile model managers"""
        # Create profiles with different roles
        student_profiles = [UserProfileFactory(role='student') for _ in range(3)]
        teacher_profiles = [UserProfileFactory(role='teacher') for _ in range(2)]
        admin_profiles = [UserProfileFactory(role='admin') for _ in range(1)]
        
        # Test default manager
        all_profiles = UserProfile.objects.all()
        self.assertEqual(all_profiles.count(), 6)
        
        # Test custom filtering
        students = UserProfile.objects.filter(role='student')
        teachers = UserProfile.objects.filter(role='teacher')
        admins = UserProfile.objects.filter(role='admin')
        
        self.assertEqual(students.count(), 3)
        self.assertEqual(teachers.count(), 2)
        self.assertEqual(admins.count(), 1)
    
    def test_user_profile_ordering(self):
        """Test user profile ordering"""
        # Create profiles with different usernames
        user1 = UserFactory(username='alice')
        user2 = UserFactory(username='bob')
        user3 = UserFactory(username='charlie')
        
        UserProfile.objects.create(user=user1, role='student')
        UserProfile.objects.create(user=user2, role='teacher')
        UserProfile.objects.create(user=user3, role='admin')
        
        # Test ordering by username
        profiles = UserProfile.objects.order_by('user__username')
        usernames = [p.user.username for p in profiles]
        self.assertEqual(usernames, sorted(usernames))
    
    def test_user_profile_aggregations(self):
        """Test user profile aggregations"""
        from django.db.models import Count
        
        # Create profiles with different roles
        for _ in range(5):
            UserProfileFactory(role='student')
        for _ in range(3):
            UserProfileFactory(role='teacher')
        for _ in range(2):
            UserProfileFactory(role='admin')
        
        # Test aggregations
        role_counts = UserProfile.objects.values('role').annotate(count=Count('id'))
        
        role_count_dict = {item['role']: item['count'] for item in role_counts}
        self.assertEqual(role_count_dict['student'], 5)
        self.assertEqual(role_count_dict['teacher'], 3)
        self.assertEqual(role_count_dict['admin'], 2)
    
    def test_user_profile_complex_queries(self):
        """Test complex queries on user profile model"""
        # Create users with different attributes
        active_student_users = []
        inactive_student_users = []
        
        for i in range(3):
            user = UserFactory(is_active=True)
            UserProfile.objects.create(user=user, role='student')
            active_student_users.append(user)
        
        for i in range(2):
            user = UserFactory(is_active=False)
            UserProfile.objects.create(user=user, role='student')
            inactive_student_users.append(user)
        
        # Complex query: Active student profiles
        active_student_profiles = UserProfile.objects.filter(
            role='student',
            user__is_active=True
        )
        
        self.assertEqual(active_student_profiles.count(), 3)
        
        # Complex query: Inactive student profiles
        inactive_student_profiles = UserProfile.objects.filter(
            role='student',
            user__is_active=False
        )
        
        self.assertEqual(inactive_student_profiles.count(), 2)
    
    def test_user_profile_database_functions(self):
        """Test database functions with user profile model"""
        from django.db.models import Upper, Lower
        
        # Create profiles with different usernames
        user1 = UserFactory(username='alice')
        user2 = UserFactory(username='BOB')
        user3 = UserFactory(username='Charlie')
        
        UserProfile.objects.create(user=user1, role='student')
        UserProfile.objects.create(user=user2, role='teacher')
        UserProfile.objects.create(user=user3, role='admin')
        
        # Test Upper function
        profiles = UserProfile.objects.annotate(
            upper_username=Upper('user__username')
        )
        
        for profile in profiles:
            self.assertEqual(profile.upper_username, profile.user.username.upper())
        
        # Test Lower function
        profiles = UserProfile.objects.annotate(
            lower_username=Lower('user__username')
        )
        
        for profile in profiles:
            self.assertEqual(profile.lower_username, profile.user.username.lower())
    
    def test_user_profile_performance_with_large_dataset(self):
        """Test user profile performance with large dataset"""
        # Create large number of profiles
        profiles = []
        for i in range(1000):
            user = UserFactory()
            profile = UserProfile.objects.create(user=user, role='student')
            profiles.append(profile)
        
        # Test query performance
        start_time = time.time()
        
        # Query all profiles
        all_profiles = UserProfile.objects.all()
        profile_count = all_profiles.count()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be reasonably fast
        self.assertLess(duration, 1.0, f"Query took {duration:.2f}s")
        self.assertEqual(profile_count, 1000)
    
    def test_user_profile_bulk_operations(self):
        """Test user profile bulk operations"""
        # Create test data
        users = [UserFactory() for _ in range(100)]
        
        # Bulk create profiles
        profiles_to_create = []
        for user in users:
            profiles_to_create.append(UserProfile(user=user, role='student'))
        
        start_time = time.time()
        UserProfile.objects.bulk_create(profiles_to_create)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should be efficient
        self.assertLess(duration, 2.0, f"Bulk create took {duration:.2f}s")
        
        # Verify all profiles were created
        self.assertEqual(UserProfile.objects.count(), 100)
        
        # Test bulk update
        start_time = time.time()
        UserProfile.objects.all().update(role='teacher')
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should be efficient
        self.assertLess(duration, 1.0, f"Bulk update took {duration:.2f}s")
        
        # Verify all profiles were updated
        teacher_count = UserProfile.objects.filter(role='teacher').count()
        self.assertEqual(teacher_count, 100)