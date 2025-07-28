from rest_framework import permissions

class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile'):
                return request.user.userprofile.role in ['teacher', 'admin']
            return request.user.is_superuser
        return False

class IsStudentOrTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile'):
                return request.user.userprofile.role in ['student', 'teacher', 'admin']
            return request.user.is_superuser
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile'):
                return request.user.userprofile.role == 'admin'
            return request.user.is_superuser
        return False