from core.models import AsistenteConsultaNoResuelta

from ..application.matching import normalize_text


class DjangoAssistantRepository:
    def register_unresolved(
        self,
        *,
        user,
        question,
        category,
        response,
        conversation=None,
        user_message=None,
        intent="",
        tool="",
        metadata=None,
    ):
        profile = getattr(user, "perfil", None)
        if profile is None:
            raise ValueError("El usuario no tiene perfil operativo.")
        return AsistenteConsultaNoResuelta.objects.create(
            conversacion=conversation,
            mensaje=user_message,
            usuario=user,
            sucursal=profile.sucursal,
            pregunta=question,
            pregunta_normalizada=normalize_text(question),
            categoria=category,
            intencion=intent or "",
            herramienta=tool or "",
            respuesta=response or "",
            metadata=metadata or {},
        )
