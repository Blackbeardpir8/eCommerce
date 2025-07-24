from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from store.models import *
from store.forms import CategoryForm, SubCategoryForm, ProductForm
from django.utils.html import format_html
from django.urls import reverse

# Unregister the default User admin
admin.site.unregister(User)

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('user_type', 'phone', 'address')

# Enhanced User Admin with Profile
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__user_type')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone')
    ordering = ('-date_joined',)
    
    def get_user_type(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.user_type == 'customer':
                return format_html('<span style="color: #007bff; font-weight: bold;">🛒 Customer</span>')
            elif obj.profile.user_type == 'supplier':
                return format_html('<span style="color: #28a745; font-weight: bold;">🏪 Supplier</span>')
        return format_html('<span style="color: #6c757d;">No Profile</span>')
    get_user_type.short_description = 'User Type'
    get_user_type.admin_order_field = 'profile__user_type'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

# UserProfile Admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'user_type', 'phone', 'get_email')
    list_filter = ('user_type',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')
    raw_id_fields = ('user',)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

# Inline for Product Images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    inlines = [ProductImageInline]
    list_display = ('name', 'get_price', 'category', 'subcategory', 'get_stock_status', 'created_by', 'get_supplier_type', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'created_by__username', 'created_by__first_name', 'created_by__last_name')
    list_filter = ('category', 'subcategory', 'created_at', 'created_by__profile__user_type')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'subcategory')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_price(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.price)
    get_price.short_description = 'Price'
    get_price.admin_order_field = 'price'
    
    def get_stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠️ Out of Stock</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color: #ffc107; font-weight: bold;">⚡ Low Stock ({})</span>', obj.stock)
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ In Stock ({})</span>', obj.stock)
    get_stock_status.short_description = 'Stock Status'
    get_stock_status.admin_order_field = 'stock'
    
    def get_supplier_type(self, obj):
        if hasattr(obj.created_by, 'profile'):
            return format_html('<span style="color: #007bff;">🏪 Supplier</span>')
        return format_html('<span style="color: #6c757d;">Unknown</span>')
    get_supplier_type.short_description = 'Seller Type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'subcategory', 'created_by', 'created_by__profile')

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_display = ('name', 'get_image_preview', 'get_products_count', 'get_subcategories_count')
    readonly_fields = ('slug', 'get_image_preview')
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    get_image_preview.short_description = 'Image Preview'
    
    def get_products_count(self, obj):
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:store_product_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #007bff; font-weight: bold;">{} Products</a>', url, count)
        return "0 Products"
    get_products_count.short_description = 'Products'
    
    def get_subcategories_count(self, obj):
        count = obj.subcategories.count()
        if count > 0:
            url = reverse('admin:store_subcategory_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #28a745; font-weight: bold;">{} Subcategories</a>', url, count)
        return "0 Subcategories"
    get_subcategories_count.short_description = 'Subcategories'

# SubCategory Admin
class SubCategoryAdmin(admin.ModelAdmin):
    form = SubCategoryForm
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'get_products_count')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    readonly_fields = ('slug',)
    
    def get_products_count(self, obj):
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:store_product_changelist') + f'?subcategory__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #007bff; font-weight: bold;">{} Products</a>', url, count)
        return "0 Products"
    get_products_count.short_description = 'Products'

# ProductImage Admin
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_image_preview', 'image')
    list_filter = ('product__category',)
    search_fields = ('product__name',)
    raw_id_fields = ('product',)
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    get_image_preview.short_description = 'Preview'

# Cart Admin
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'get_subtotal')
    readonly_fields = ('get_subtotal',)
    raw_id_fields = ('product',)
    
    def get_subtotal(self, obj):
        if obj.product and obj.quantity:
            return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.subtotal())
        return "₹0"
    get_subtotal.short_description = 'Subtotal'

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('user', 'get_user_type', 'get_items_count', 'get_total_amount')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__profile__user_type',)
    
    def get_user_type(self, obj):
        if hasattr(obj.user, 'profile'):
            return format_html('<span style="color: #007bff;">🛒 Customer</span>')
        return "Unknown"
    get_user_type.short_description = 'User Type'
    
    def get_items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold;">{} Items</span>', count)
    get_items_count.short_description = 'Items'
    
    def get_total_amount(self, obj):
        total = obj.total()
        return format_html('<span style="color: #28a745; font-weight: bold; font-size: 1.1em;">₹{}</span>', total)
    get_total_amount.short_description = 'Total Amount'

# CartItem Admin
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'product', 'quantity', 'get_subtotal', 'get_stock_check')
    list_filter = ('cart__user__profile__user_type', 'product__category')
    search_fields = ('cart__user__username', 'product__name')
    raw_id_fields = ('cart', 'product')
    
    def get_user(self, obj):
        return obj.cart.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'cart__user__username'
    
    def get_subtotal(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.subtotal())
    get_subtotal.short_description = 'Subtotal'
    
    def get_stock_check(self, obj):
        if obj.quantity > obj.product.stock:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠️ Exceeds Stock</span>')
        return format_html('<span style="color: #28a745;">✅ OK</span>')
    get_stock_check.short_description = 'Stock Check'

# Wishlist Admin
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    fields = ('product', 'added_at', 'get_product_price', 'get_stock_status')
    readonly_fields = ('added_at', 'get_product_price', 'get_stock_status')
    raw_id_fields = ('product',)
    
    def get_product_price(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.product.price)
    get_product_price.short_description = 'Price'
    
    def get_stock_status(self, obj):
        if obj.product.stock == 0:
            return format_html('<span style="color: #dc3545;">Out of Stock</span>')
        return format_html('<span style="color: #28a745;">In Stock ({})</span>', obj.product.stock)
    get_stock_status.short_description = 'Stock'

class WishlistAdmin(admin.ModelAdmin):
    inlines = [WishlistItemInline]
    list_display = ('user', 'get_user_type', 'get_items_count', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__profile__user_type', 'created_at')
    date_hierarchy = 'created_at'
    
    def get_user_type(self, obj):
        if hasattr(obj.user, 'profile'):
            return format_html('<span style="color: #007bff;">🛒 Customer</span>')
        return "Unknown"
    get_user_type.short_description = 'User Type'
    
    def get_items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold;">{} Items</span>', count)
    get_items_count.short_description = 'Items'

# WishlistItem Admin
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'product', 'get_product_price', 'get_stock_status', 'added_at')
    list_filter = ('wishlist__user__profile__user_type', 'product__category', 'added_at')
    search_fields = ('wishlist__user__username', 'product__name')
    raw_id_fields = ('wishlist', 'product')
    date_hierarchy = 'added_at'
    
    def get_user(self, obj):
        return obj.wishlist.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'wishlist__user__username'
    
    def get_product_price(self, obj):
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', obj.product.price)
    get_product_price.short_description = 'Price'
    
    def get_stock_status(self, obj):
        if obj.product.stock == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠️ Out of Stock</span>')
        elif obj.product.stock <= 5:
            return format_html('<span style="color: #ffc107; font-weight: bold;">⚡ Low Stock</span>')
        return format_html('<span style="color: #28a745;">✅ In Stock</span>')
    get_stock_status.short_description = 'Stock Status'

# Register models with enhanced admin
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(WishlistItem, WishlistItemAdmin)

# Customize admin site header and title
admin.site.site_header = "eCommerce Administration"
admin.site.site_title = "eCommerce Admin"
admin.site.index_title = "Welcome to eCommerce Administration"