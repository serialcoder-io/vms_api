from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

class VoucherRequestPagination(PageNumberPagination):
    page_size = 4
    max_page_size = 100

class VoucherPagination(PageNumberPagination):
    page_size = 4
    max_page_size = 100


class ClientsPagination(PageNumberPagination):
    page_size = 4
    max_page_size = 100