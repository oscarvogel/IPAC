from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AlumnoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    allowed_page_sizes = (5, 10, 25)

    def get_page_size(self, request):
        requested = request.query_params.get(self.page_size_query_param)
        try:
            requested = int(requested)
        except (TypeError, ValueError):
            return self.page_size
        return requested if requested in self.allowed_page_sizes else self.page_size

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.page.paginator.per_page,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
