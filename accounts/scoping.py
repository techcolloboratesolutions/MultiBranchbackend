from rest_framework.exceptions import PermissionDenied

INSTITUTION_FORBIDDEN = "You are not authorized to access this institution."


def _to_int(value):
    if value in (None, "", "all", "ALL"):
        return None
    return int(value)


def requested_institution_id(request):
    raw = (
        request.query_params.get("institution_id")
        if hasattr(request, "query_params")
        else None
    )
    if raw in (None, "") and hasattr(request, "data"):
        raw = request.data.get("institution_id", request.data.get("institution"))
        if hasattr(raw, "id"):
            raw = raw.id
    return _to_int(raw)


def scoped_institution_id(request, requested=None):
    """
    MANAGER: always own institution; other ids -> 403.
    ADMIN: None means all institutions; otherwise the requested id.
    """
    user = request.user
    if requested is None:
        requested = requested_institution_id(request)

    if getattr(user, "is_manager_role", False):
        if requested is not None and requested != user.institution_id:
            raise PermissionDenied(detail=INSTITUTION_FORBIDDEN)
        return user.institution_id

    return requested


def apply_institution_filter(queryset, request, field="institution_id"):
    institution_id = scoped_institution_id(request)
    if institution_id is not None:
        return queryset.filter(**{field: institution_id})
    return queryset
