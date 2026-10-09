from rest_framework.exceptions import PermissionDenied

from institutions.models import Institution

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


def _chief_institution_ids(user):
    return set(
        Institution.objects.filter(
            main_institution_id=user.main_institution_id
        ).values_list("pk", flat=True)
    )


def scoped_institution_id(request, requested=None):
    """
    MANAGER: always own institution; other ids -> 403.
    CHIEF_MANAGER: a branch under their main institution, or None for all of those branches.
    ADMIN: None means every institution; otherwise the requested id.
    """
    user = request.user
    if requested is None:
        requested = requested_institution_id(request)

    if getattr(user, "is_manager_role", False):
        if requested is not None and requested != user.institution_id:
            raise PermissionDenied(detail=INSTITUTION_FORBIDDEN)
        return user.institution_id

    if getattr(user, "is_chief_manager_role", False):
        if requested is not None and requested not in _chief_institution_ids(user):
            raise PermissionDenied(detail=INSTITUTION_FORBIDDEN)
        return requested

    return requested


def scoped_main_institution_id(request, institution_id):
    """
    When a chief manager asks for every branch, limit totals to their main institution.
    A specific branch id needs no extra main filter.
    """
    if institution_id is not None:
        return None
    user = request.user
    if getattr(user, "is_chief_manager_role", False):
        return user.main_institution_id
    return None


def apply_institution_filter(queryset, request, field="institution_id"):
    institution_id = scoped_institution_id(request)
    if institution_id is not None:
        return queryset.filter(**{field: institution_id})
    main_institution_id = scoped_main_institution_id(request, institution_id)
    if main_institution_id is not None:
        if field == "institution_id":
            return queryset.filter(institution__main_institution_id=main_institution_id)
        if field in ("pk", "id"):
            return queryset.filter(main_institution_id=main_institution_id)
    return queryset
