from rest_framework.permissions import BasePermission


class IsTeacherOrAdmin(BasePermission):
    """Allow only users with role teacher or admin."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("teacher", "admin")
        )


class IsOwnerOrTeacher(BasePermission):
    """Allow access to own data, or teacher/admin to any."""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ("teacher", "admin"):
            return True
        return obj.user == request.user
