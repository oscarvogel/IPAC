from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    profile = getattr(getattr(request, "user", None), "perfil", None)

    if response is not None and response.status_code == 403 and getattr(profile, "debe_cambiar_clave", False):
        response.data = {
            "detail": "Debe cambiar su clave antes de continuar.",
            "code": "password_change_required",
        }

    return response
