from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product,ProductImage, Cart, CartItem
from store.forms import RegisterForm , LoginForm, ProductForm,ProductImageFormSet
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator

# Create your views here.

def home(request):
    return render(request, 'store/home.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # hash password
            user.save()
            messages.success(request, 'Account created! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



#products add
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()

            for image_form in formset.cleaned_data:
                if image_form and image_form.get('image'):
                    ProductImage.objects.create(product=product, image=image_form['image'])

            messages.success(request, "Product and images added successfully.")
            return redirect('product_list')
    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add Product',
    })


# All products list
def product_list(request):
    products = Product.objects.all().order_by('-id')
    paginator = Paginator(products, 5)  # Show 5 per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, 'store/product_list.html', {'products': products})



#update product




def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.filter(product=product))
        if form.is_valid() and formset.is_valid():
            form.save()

            for image_form in formset:
                if image_form.cleaned_data and image_form.cleaned_data.get('image'):
                    ProductImage.objects.create(product=product, image=image_form.cleaned_data['image'])

            messages.success(request, "Product and images updated.")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(queryset=ProductImage.objects.filter(product=product))

    return render(request, 'store/product_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Product',
    })


# Delete product
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect('product_list')
    return render(request, 'store/product_confirm_delete.html', {'product': product})


# Cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart_view')

# view
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    total = cart.total()

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total,
    })

#remove cart 
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart_view')


#update cart
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart_view')