from django.urls import path
from .views import product_list, add_to_cart, cart, checkout, success, cancel, remove_from_cart

urlpatterns = [
    path('', product_list, name='product_list'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('success/', success, name='success'),
    path('cancel/', cancel, name='cancel'),
    path('cart/remove/<str:product_id>/', remove_from_cart, name='remove_from_cart'), 
    path('remove-from-cart/<str:product_id>/', remove_from_cart, name='remove_from_cart'),

]
