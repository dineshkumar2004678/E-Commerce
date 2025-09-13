from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import ProductManager, Cart, CartItem, Order
from .forms import UserRegistrationForm, LoginForm
from bson import ObjectId
import json

def index(request):
    products = ProductManager.get_all_products()
    
    # Convert MongoDB _id to string for each product
    if products:
        for product in products:
            product['id_str'] = str(product['_id'])
    
    categories = set()
    for product in products:
        categories.add(product.get('category', ''))
    
    return render(request, 'ecommerce_app/index.html', {
        'products': products,
        'categories': categories,
    })

def product_detail(request, product_id):
    product = ProductManager.get_product_by_id(product_id)
    if not product:
        messages.error(request, "Product not found.")
        return redirect('index')
    
    # Convert _id to string
    product['id_str'] = str(product['_id'])
    
    # Get related products and convert their _id too
    related_products = ProductManager.get_products_by_category(product.get('category', ''))
    for related in related_products:
        related['id_str'] = str(related['_id'])
    
    # Filter out the current product from related products
    filtered_related = []
    for related in related_products:
        if str(related.get('_id', '')) != product_id and len(filtered_related) < 4:
            filtered_related.append(related)
    
    return render(request, 'ecommerce_app/product_detail.html', {
        'product': product,
        'related_products': filtered_related
    })

def category_products(request, category):
    products = ProductManager.get_products_by_category(category)
    
    # Convert _id to string for each product
    for product in products:
        product['id_str'] = str(product['_id'])
    
    return render(request, 'ecommerce_app/category.html', {
        'products': products,
        'category': category
    })

def search_products(request):
    query = request.GET.get('query', '')
    products = ProductManager.search_products(query)
    
    # Convert _id to string for each product
    for product in products:
        product['id_str'] = str(product['_id'])
    
    return render(request, 'ecommerce_app/search.html', {
        'products': products,
        'query': query
    })

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a cart for the new user
            Cart.objects.create(user=user)
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('index')
    else:
        form = UserRegistrationForm()
    return render(request, 'ecommerce_app/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'ecommerce_app/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('index')

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'ecommerce_app/cart.html', {
        'cart': cart
    })

@require_POST
@csrf_exempt
@login_required
def add_to_cart(request, product_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product = ProductManager.get_product_by_id(product_id)
    
    if not product:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    
    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product_id=product_id,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({
        'success': True, 
        'message': 'Product added to cart',
        'cart_item_count': cart.item_count
    })

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        return redirect('cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    
    # Create order
    order_items = []
    for item in cart.items.all():
        product = item.product
        if product:
            order_items.append({
                'product_id': str(product.get('_id', '')),
                'title': product.get('title', ''),
                'price': float(product.get('price', 0)),
                'quantity': item.quantity,
                'image': product.get('image', '')
            })
    
    order = Order.objects.create(
        user=request.user,
        items=order_items,
        total_price=cart.total_price
    )
    
    # Clear cart
    cart.items.all().delete()
    
    messages.success(request, f"Order placed successfully! Your order ID is #{order.id}.")
    return redirect('index')