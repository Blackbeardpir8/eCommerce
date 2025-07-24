# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Supplier URLs
    path('supplier/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),
    path('supplier/products/', views.supplier_products, name='supplier_products'),
    path('supplier/products/add/', views.add_product, name='add_product'),
    
    # Product URLs (Public)
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Product Management URLs (Supplier only)
    path('products/<slug:slug>/edit/', views.edit_product_by_slug, name='edit_product'),
    path('products/<slug:slug>/delete/', views.delete_product_by_slug, name='delete_product'),
    
    # Category URLs
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_products, name='subcategory_products'),

    # Cart URLs (Customer only)
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),

    # Wishlist URLs (Customer only)
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
    
    # AJAX URLs
    path('ajax/load-subcategories/', views.load_subcategories, name='ajax_load_subcategories'),
]