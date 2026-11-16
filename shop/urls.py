from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrito/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('carrito/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
]
