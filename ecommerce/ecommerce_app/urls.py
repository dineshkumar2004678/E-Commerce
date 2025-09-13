from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),
    path('category/<str:category>/', views.category_products, name='category'),
    path('search/', views.search_products, name='search'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
]