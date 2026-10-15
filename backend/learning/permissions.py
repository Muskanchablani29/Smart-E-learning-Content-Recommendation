from rest_framework import permissions
from .models import User


class IsStudent(permissions.BasePermission):
    """Allows access only to authenticated students."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.STUDENT
        )


class IsInstructor(permissions.BasePermission):
    """Allows access to instructors or admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or request.user.is_staff)
        )


class IsAdminUserRole(permissions.BasePermission):
    """Allows access only to users with the Admin role or staff."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.ADMIN or request.user.is_staff or request.user.is_superuser)
        )


class IsInstructorOrReadOnly(permissions.BasePermission):
    """Read-only for students, write for instructors and admins."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.INSTRUCTOR, User.Role.ADMIN] or request.user.is_staff)
        )
