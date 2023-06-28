from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

site_slug_parameter = OpenApiParameter(
    name="site_slug", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
)
id_parameter = OpenApiParameter(
    name="id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
)
