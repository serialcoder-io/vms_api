from rest_framework.pagination import PageNumberPagination

class VoucherRequestPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100

class VoucherPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ClientsPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class UserPagination(PageNumberPagination):
    page_size = 15
    max_page_size = 100

class CompanyPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100

class ShopPagination(PageNumberPagination):
    page_size = 15
    max_page_size = 100