from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    message = "An error occurred."
    if isinstance(detail, dict):
        if "detail" in detail:
            message = str(detail["detail"])
        else:
            parts = []
            for key, value in detail.items():
                if isinstance(value, list):
                    parts.append(f"{key}: {value[0]}")
                else:
                    parts.append(f"{key}: {value}")
            if parts:
                message = "; ".join(parts)
    elif isinstance(detail, list) and detail:
        message = str(detail[0])
    else:
        message = str(detail)

    response.data = {"detail": message, "status": response.status_code}
    return response
