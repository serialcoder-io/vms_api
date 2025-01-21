from rest_framework.pagination import PageNumberPagination

class UsersPagination(PageNumberPagination):
    page_size = 4
    max_page_size = 100