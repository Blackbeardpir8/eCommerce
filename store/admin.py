from django.contrib import admin
from store.models import *

# Register your models here.

# Inline for Product Images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Show one empty image field by default

# Admin for Product
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'price', 'category', 'subcategory', 'stock', 'created_by')
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug
    search_fields = ('name', 'description')
    list_filter = ('category', 'subcategory')
    readonly_fields = ('slug',)

# Admin for Category
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('slug',)

# Admin for SubCategory
class SubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)
    readonly_fields = ('slug',)

# Register models 
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)  

