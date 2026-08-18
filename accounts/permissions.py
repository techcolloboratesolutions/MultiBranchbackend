from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_admin_role", False))


class IsManagerRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_manager_role", False))


class IsAdminOrReadOnlyManager(BasePermission):
    """Admin can mutate catalogs; managers may read."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_admin_role", False):
            return True
        if getattr(user, "is_manager_role", False) and request.method in SAFE_METHODS:
            return True
        return False


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "is_admin_role", False) or getattr(user, "is_manager_role", False))
        )
