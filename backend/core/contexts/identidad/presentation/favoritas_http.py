from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from core.permissions import RolePermission, ALL_ROLES
from ..application.consultas_favoritas import ConsultasFavoritas
from ..domain.consulta_favorita import FavoritaInvalida, FavoritaNoEncontrada
from ..infrastructure.django_favoritas import DjangoFavoritasRepository, DjangoAlcanceConsultas


def contrato(favorita):
    return {"id": favorita.id, "nombre": favorita.nombre, "pantalla": favorita.pantalla, "configuracion": favorita.configuracion}


class FavoritasPermission(RolePermission):
    write_roles = ALL_ROLES


class ConsultaFavoritaViewSet(viewsets.ViewSet):
    lookup_value_regex = r"\d+"
    permission_classes = [FavoritasPermission]

    def ejecutar(self, comando, **kwargs):
        # Composición en el borde HTTP. Ningún controlador accede al repositorio.
        caso = ConsultasFavoritas(DjangoFavoritasRepository(), DjangoAlcanceConsultas())
        try:
            return getattr(caso, comando)(actor_id=self.request.user.id, **kwargs)
        except FavoritaInvalida as error:
            raise ValidationError({"detail": str(error)})
        except FavoritaNoEncontrada:
            raise NotFound("Consulta favorita no encontrada.")

    def list(self, request):
        return Response([contrato(item) for item in self.ejecutar("listar", pantalla=request.query_params.get("pantalla"))])

    def retrieve(self, request, pk=None):
        return Response(contrato(self.ejecutar("obtener", id=pk)))

    def create(self, request):
        return Response(contrato(self.ejecutar("guardar", datos=request.data)), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(contrato(self.ejecutar("guardar", id=pk, datos=request.data)))

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        self.ejecutar("eliminar", id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
