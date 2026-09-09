class CambiarClave:
    """Caso de uso para reemplazar una clave temporal del usuario autenticado."""

    def execute(self, *, user, profile, new_password):
        user.set_password(new_password)
        user.save(update_fields=["password"])
        profile.debe_cambiar_clave = False
        profile.save(update_fields=["debe_cambiar_clave", "actualizado"])
