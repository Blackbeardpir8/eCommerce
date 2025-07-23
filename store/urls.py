from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Product URLs with slugs
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('products/<slug:slug>/edit/', views.edit_product_by_slug, name='edit_product'),
    path('products/<slug:slug>/delete/', views.delete_product_by_slug, name='delete_product'),
    
    # Category URLs with slugs
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_products, name='subcategory_products'),

    # Cart URLs
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
]