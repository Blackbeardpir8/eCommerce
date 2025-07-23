from django.contrib import admin
from store.models import *
from store.forms import CategoryForm, SubCategoryForm, ProductForm

# Inline for Product Images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    inlines = [ProductImageInline]
    list_display = ('name', 'price', 'category', 'subcategory', 'stock', 'created_by')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('category', 'subcategory')
    #readonly_fields = ('slug',)

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    #readonly_fields = ('slug',)

# SubCategory Admin
class SubCategoryAdmin(admin.ModelAdmin):
    form = SubCategoryForm
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)
    #readonly_fields = ('slug',)

# Register models
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
