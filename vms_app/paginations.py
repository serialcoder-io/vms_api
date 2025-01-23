from rest_framework.pagination import PageNumberPagination

class VoucherRequestPagination(PageNumberPagination):
    page_size = 4
    max_page_size = 100