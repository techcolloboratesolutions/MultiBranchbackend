from rest_framework.permissions import BasePermission, SAFE_METHODS


def _user(request):
    user = request.user
    if not user or not user.is_authenticated:
        return None
    return user


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        user = _user(request)
        return bool(user and getattr(user, "is_admin_role", False))


class IsManagerRole(BasePermission):
    def has_permission(self, request, view):
        user = _user(request)
        return bool(user and getattr(user, "is_manager_role", False))


class IsAdminOrChiefManager(BasePermission):
    """Admin, or a chief manager scoped to one main institution."""

    def has_permission(self, request, view):
        user = _user(request)
        return bool(
            user
            and (
                getattr(user, "is_admin_role", False)
                or getattr(user, "is_chief_manager_role", False)
            )
        )


class IsAdminOrReadOnlyManager(BasePermission):
    """Admin can mutate catalogs such as heads. Managers and chief managers may read."""

    def has_permission(self, request, view):
        user = _user(request)
        if user is None:
            return False
        if getattr(user, "is_admin_role", False):
            return True
        if request.method in SAFE_METHODS and (
            getattr(user, "is_manager_role", False)
            or getattr(user, "is_chief_manager_role", False)
        ):
            return True
        return False


class IsAdminOrChiefOrReadOnlyManager(BasePermission):
    """Partners: admin and chief manager can mutate; branch managers may read."""

    def has_permission(self, request, view):
        user = _user(request)
        if user is None:
            return False
        if getattr(user, "is_admin_role", False) or getattr(user, "is_chief_manager_role", False):
            return True
        if getattr(user, "is_manager_role", False) and request.method in SAFE_METHODS:
            return True
        return False


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        user = _user(request)
        return bool(
            user
            and (
                getattr(user, "is_admin_role", False)
                or getattr(user, "is_manager_role", False)
                or getattr(user, "is_chief_manager_role", False)
            )
        )
