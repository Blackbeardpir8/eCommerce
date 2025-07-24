from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, ProductImage, Cart, CartItem, Category, SubCategory, UserProfile, Wishlist, WishlistItem
from store.forms import RegisterForm, LoginForm, ProductForm, ProductImageFormSet
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import transaction

# Helper functions for better code organization
def get_user_type(user):
    """Get user type safely"""
    if not user.is_authenticated:
        return None
    try:
        return user.profile.user_type
    except (AttributeError, UserProfile.DoesNotExist):
        return None

def is_supplier(user):
    """Check if user is a supplier"""
    return get_user_type(user) == 'supplier'

def is_customer_or_anonymous(user):
    """Check if user is customer or anonymous (can use cart/wishlist)"""
    user_type = get_user_type(user)
    return user_type == 'customer' or user_type is None or not user.is_authenticated

def home(request):
    """Home page with product search and filtering"""
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all().order_by('-created_at')

    if query:
        products = products.filter(name__icontains=query)

    # Add proper validation for price filters
    try:
        if min_price:
            min_price_val = float(min_price)
            products = products.filter(price__gte=min_price_val)
    except (ValueError, TypeError):
        min_price = ''
        
    try:
        if max_price:
            max_price_val = float(max_price)
            products = products.filter(price__lte=max_price_val)
    except (ValueError, TypeError):
        max_price = ''

    return render(request, 'store/home.html', {
        'products': products,
        'query': query or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
    })

def register_view(request):
    """Enhanced registration with user type selection"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Account created as {form.cleaned_data["user_type"]}! Please login.')
                return redirect('login')
            except Exception as e:
                messages.error(request, 'Error creating account. Please try again.')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    """Custom login with redirect based on user type"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirect based on user type
            if is_supplier(user):
                return redirect('supplier_dashboard')
            else:
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

# SUPPLIER VIEWS

def supplier_dashboard(request):
    """Dashboard for suppliers"""
    if not is_supplier(request.user):
        messages.error(request, 'Access denied. Suppliers only.')
        return redirect('home')
    
    try:
        products = Product.objects.filter(created_by=request.user).order_by('-created_at')
        total_products = products.count()
        out_of_stock = products.filter(stock=0).count()
        
        return render(request, 'store/supplier_dashboard.html', {
            'products': products[:5],  # Show latest 5 products
            'total_products': total_products,
            'out_of_stock': out_of_stock,
        })
    except Exception as e:
        messages.error(request, 'Error loading dashboard.')
        return redirect('home')

def supplier_products(request):
    """List all products for supplier"""
    if not is_supplier(request.user):
        messages.error(request, 'Access denied. Suppliers only.')
        return redirect('home')
    
    try:
        products = Product.objects.filter(created_by=request.user).order_by('-created_at')
        paginator = Paginator(products, 10)
        page = request.GET.get('page')
        products = paginator.get_page(page)
        
        return render(request, 'store/supplier_products.html', {'products': products})
    except Exception as e:
        messages.error(request, 'Error loading products.')
        return redirect('supplier_dashboard')

@transaction.atomic
def add_product(request):
    """Add product - suppliers only"""
    if not is_supplier(request.user):
        messages.error(request, 'Access denied. Suppliers only.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        
        if form.is_valid() and formset.is_valid():
            try:
                product = form.save(commit=False)
                product.created_by = request.user
                product.save()

                # Handle image uploads with error checking
                for image_form in formset.cleaned_data:
                    if image_form and image_form.get('image') and not image_form.get('DELETE'):
                        try:
                            ProductImage.objects.create(product=product, image=image_form['image'])
                        except Exception as e:
                            messages.warning(request, f'Error uploading one of the images: {str(e)}')

                messages.success(request, "Product added successfully.")
                return redirect('supplier_products')
                
            except Exception as e:
                messages.error(request, 'Error creating product. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add Product',
    })

def product_list(request):
    """Public product listing for all users"""
    try:
        products = Product.objects.all().order_by('-created_at')
        paginator = Paginator(products, 12)
        page = request.GET.get('page')
        products = paginator.get_page(page)
        return render(request, 'store/product_list.html', {'products': products})
    except Exception as e:
        messages.error(request, 'Error loading products.')
        return render(request, 'store/product_list.html', {'products': []})

def product_detail(request, slug):
    """Product detail view"""
    product = get_object_or_404(Product, slug=slug)
    
    # Check if product is in user's wishlist - with proper error handling
    in_wishlist = False
    if request.user.is_authenticated:
        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            in_wishlist = WishlistItem.objects.filter(wishlist=wishlist, product=product).exists()
        except Exception as e:
            # Continue without wishlist status if there's an error
            pass
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'in_wishlist': in_wishlist
    })

@transaction.atomic
def edit_product_by_slug(request, slug):
    """Edit product - only by owner"""
    product = get_object_or_404(Product, slug=slug)
    
    # Check ownership
    if not request.user.is_authenticated or product.created_by != request.user:
        messages.error(request, 'You can only edit your own products.')
        return redirect('product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.filter(product=product))
        
        if form.is_valid() and formset.is_valid():
            try:
                form.save()

                # Handle image updates with better error handling
                for image_form in formset:
                    if image_form.cleaned_data:
                        try:
                            if image_form.cleaned_data.get('DELETE'):
                                if image_form.instance.pk:
                                    image_form.instance.delete()
                            elif image_form.cleaned_data.get('image'):
                                if image_form.instance.pk:
                                    image_form.save()
                                else:
                                    ProductImage.objects.create(product=product, image=image_form.cleaned_data['image'])
                        except Exception as e:
                            messages.warning(request, f'Error processing image: {str(e)}')

                messages.success(request, "Product updated successfully.")
                return redirect('supplier_products')
                
            except Exception as e:
                messages.error(request, 'Error updating product. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(queryset=ProductImage.objects.filter(product=product))

    return render(request, 'store/product_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Product',
        'product': product
    })

def delete_product_by_slug(request, slug):
    """Delete product - only by owner"""
    product = get_object_or_404(Product, slug=slug)
    
    # Check ownership
    if not request.user.is_authenticated or product.created_by != request.user:
        messages.error(request, 'You can only delete your own products.')
        return redirect('product_list')
    
    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, "Product deleted successfully.")
        except Exception as e:
            messages.error(request, 'Error deleting product. Please try again.')
        return redirect('supplier_products')
        
    return render(request, 'store/product_confirm_delete.html', {'product': product})

# CATEGORY VIEWS
def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    try:
        products = Product.objects.filter(category=category)
        return render(request, 'store/category_products.html', {
            'category': category,
            'products': products,
        })
    except Exception as e:
        messages.error(request, 'Error loading category products.')
        return redirect('home')

def subcategory_products(request, category_slug, subcategory_slug):
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
    
    try:
        products = Product.objects.filter(subcategory=subcategory)
        return render(request, 'store/subcategory_products.html', {
            'category': category,
            'subcategory': subcategory,
            'products': products,
        })
    except Exception as e:
        messages.error(request, 'Error loading subcategory products.')
        return redirect('category_products', category_slug=category_slug)

# CART VIEWS

@transaction.atomic
def add_to_cart(request, product_id):
    """Add product to cart - customers only"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add items to cart.')
        return redirect('login')
    
    # Check if user is supplier
    if is_supplier(request.user):
        messages.error(request, 'Suppliers cannot add products to cart.')
        return redirect('product_list')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check stock availability
    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect('product_detail', slug=product.slug)
    
    try:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            # Check if adding one more would exceed stock
            if cart_item.quantity >= product.stock:
                messages.error(request, f"Cannot add more {product.name}. Stock limit reached.")
            else:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"{product.name} quantity updated in cart.")
        else:
            # New item, quantity is 1 by default, already checked stock > 0
            messages.success(request, f"{product.name} added to cart.")

    except Exception as e:
        messages.error(request, 'Error adding product to cart. Please try again.')
    
    return redirect('cart_view')

def cart_view(request):
    """View cart - customers only"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view your cart.')
        return redirect('login')
    
    # Check if user is supplier
    if is_supplier(request.user):
        messages.error(request, 'Suppliers cannot view cart.')
        return redirect('supplier_dashboard')
    
    try:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product')
        total = cart.total()

        return render(request, 'store/cart.html', {
            'items': items,
            'total': total,
        })
    except Exception as e:
        messages.error(request, 'Error loading cart.')
        return render(request, 'store/cart.html', {
            'items': [],
            'total': 0,
        })

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    try:
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = item.product.name
        item.delete()
        messages.success(request, f"{product_name} removed from cart.")
    except Exception as e:
        messages.error(request, 'Error removing item from cart.')
    
    return redirect('cart_view')

@transaction.atomic
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0:
                item.delete()
                messages.success(request, "Item removed from cart.")
            elif quantity > item.product.stock:
                messages.error(request, f"Only {item.product.stock} items available.")
            else:
                item.quantity = quantity
                item.save()
                messages.success(request, "Cart updated.")
                
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity.')
        except Exception as e:
            messages.error(request, 'Error updating cart.')
    
    return redirect('cart_view')

# WISHLIST VIEWS

def add_to_wishlist(request, product_id):
    """Add product to wishlist - customers only"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add items to wishlist.')
        return redirect('login')
    
    # Check if user is supplier
    if is_supplier(request.user):
        messages.error(request, 'Suppliers cannot use wishlist.')
        return redirect('product_list')
    
    product = get_object_or_404(Product, id=product_id)
    
    try:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
        
        if created:
            messages.success(request, f"{product.name} added to wishlist.")
        else:
            messages.info(request, f"{product.name} is already in your wishlist.")
            
    except Exception as e:
        messages.error(request, 'Error adding to wishlist. Please try again.')
    
    return redirect('product_detail', slug=product.slug)

def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    
    try:
        wishlist = get_object_or_404(Wishlist, user=request.user)
        wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
        wishlist_item.delete()
        messages.success(request, f"{product.name} removed from wishlist.")
    except WishlistItem.DoesNotExist:
        messages.error(request, "Product not found in wishlist.")
    except Exception as e:
        messages.error(request, 'Error removing from wishlist.')
    
    return redirect('wishlist_view')

def wishlist_view(request):
    """View wishlist - customers only"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view your wishlist.')
        return redirect('login')
    
    # Check if user is supplier
    if is_supplier(request.user):
        messages.error(request, 'Suppliers cannot view wishlist.')
        return redirect('supplier_dashboard')
    
    try:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        items = wishlist.items.select_related('product')
        
        return render(request, 'store/wishlist.html', {
            'items': items,
        })
    except Exception as e:
        messages.error(request, 'Error loading wishlist.')
        return render(request, 'store/wishlist.html', {
            'items': [],
        })

@transaction.atomic
def move_to_cart(request, product_id):
    """Move product from wishlist to cart"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    # Check if user is supplier
    if is_supplier(request.user):
        messages.error(request, 'Suppliers cannot use cart.')
        return redirect('supplier_dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check stock availability
    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock and cannot be added to cart.")
        return redirect('wishlist_view')
    
    try:
        # Remove from wishlist
        wishlist = get_object_or_404(Wishlist, user=request.user)
        try:
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
            wishlist_item.delete()
        except WishlistItem.DoesNotExist:
            pass  # Item not in wishlist, continue anyway
        
        # Add to cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            if cart_item.quantity < product.stock:
                cart_item.quantity += 1
                cart_item.save()
        
        messages.success(request, f"{product.name} moved to cart.")
        
    except Exception as e:
        messages.error(request, 'Error moving item to cart.')
    
    return redirect('wishlist_view')

# AJAX VIEW for dynamic subcategory loading
def load_subcategories(request):
    """Load subcategories based on selected category"""
    try:
        category_id = request.GET.get('category_id')
        if not category_id:
            return JsonResponse([], safe=False)
            
        subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
        return JsonResponse(list(subcategories.values('id', 'name')), safe=False)
    except Exception as e:
        return JsonResponse([], safe=False)