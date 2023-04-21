from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class PageNumberPagination(pagination.PageNumberPagination):
	page_size_query_param = "pageSize"
	max_page_size = 1000

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
