from collections import OrderedDict

from django.core.paginator import InvalidPage, Page, Paginator
from django.utils.functional import cached_property
from rest_framework import pagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from backend.search.utils.constants import ES_MAX_RESULTS, ES_PAGE_SIZE


class FasterCountPagination(Paginator):
    @cached_property
    def count(self):
        # Override the count property to select only the id field to speed up the count
        return self.object_list.values("id").count()


class PageNumberPagination(pagination.PageNumberPagination):
    page_size_query_param = "pageSize"
    max_page_size = 1000
    django_paginator_class = FasterCountPagination

    def get_paginated_response(self, data):
        """
        Adds a pageCount property to the paginated response.
        """
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("pages", self.page.paginator.num_pages),
                    ("pageSize", self.get_page_size(self.request)),
                    (
                        "next",
                        self.page.next_page_number() if self.page.has_next() else None,
                    ),
                    ("next_url", self.get_next_link()),
                    (
                        "previous",
                        self.page.previous_page_number()
                        if self.page.has_previous()
                        else None,
                    ),
                    ("previous_url", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class ElasticSearchPaginator(Paginator):
    """
    Overriding Django's Paginator to properly set the count of the search results and prevent slicing.
    Slicing is handled by the elastic search query.
    """

    def count(self):
        """
        Overriding count property to return the count of the search results.
        """
        return self.count

    def page(self, number):
        """
        Overriding page method to prevent slicing.
        """
        number = self.validate_number(number)
        return Page(self.object_list, number, self)

    def set_search_result_count(self, count):
        self.count = count


class SearchPageNumberPagination(PageNumberPagination):
    def __init__(self):
        self.page = None
        self.request = None
        self.page_size = ES_PAGE_SIZE
        self.max_page_size = ES_MAX_RESULTS
        self.django_paginator_class = ElasticSearchPaginator

    def apply_search_pagination(self, request, object_list, count):
        """
        A modified version of the PageNumberPagination class's paginate_queryset method.
        """

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = ElasticSearchPaginator(object_list=object_list, per_page=page_size)
        paginator.set_search_result_count(count)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    @staticmethod
    def override_invalid_number(number, override_value=1):
        """
        A modified version the Django Paginator validate_number method to set invalid page numbers to 1.
        This allows the pagination parameters to be used and the invalid page number to be caught by the
        paginator.
        """
        try:
            if isinstance(number, float) and not number.is_integer():
                return override_value
            number = int(number)
        except (TypeError, ValueError):
            return override_value
        if number < 1:
            return override_value
        return number
