from django.shortcuts import render, redirect
from .models import Product
from django.contrib.sessions.models import Session
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages

stripe.api_key = settings.STRIPE_SECRET_KEY

def product_list(request):
    products = Product.objects.all()
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    return render(request, 'store/product_list.html', {'products': products, 'total_items': cart_count})

""" Original 
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('product_list')
"""


def add_to_cart(request, product_id):
    # Retrieve the cart from the session or create an empty one if it doesn't exist
    cart = request.session.get('cart', {})

    # Ensure the product ID is a string
    product_id = str(product_id)

    # Increment the product quantity if it's already in the cart, otherwise set it to 1
    if product_id in cart:
        cart[product_id] += 1
        messages.success(request, f"Updated quantity for product {product_id}.")
    else:
        cart[product_id] = 1
        messages.success(request, f"Added product {product_id} to cart.")

    # Save the updated cart back to the session
    request.session['cart'] = cart
    request.session.modified = True  # Force session save

    # Retrieve messages
    message_list = []
    for message in messages.get_messages(request):
        message_list.append({
            'level': message.level_tag,
            'message': message.message
        })

# Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return a JSON response with a success message and the updated cart count
        return JsonResponse({
            'success': True,
            'cart_count': sum(cart.values()),  # Total items in cart
            'messages': list(messages.get_messages(request))  # Pass the messages in the response
        })
    else:
        # Redirect back to the referring page or a specific URL
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

""" Old
def cart(request):
    cart = request.session.get('cart', {})
    products = []  # A list to hold product instances
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        products.append({'product': product, 'quantity': quantity})
        total += product.price * quantity

    return render(request, 'store/cart.html', {'products': products, 'total': total})
"""

def cart(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            products.append({
                'product': product,
                'quantity': quantity,
                'total_price': product.price * quantity
            })
            total += product.price * quantity
        except Product.DoesNotExist:
            pass

    return render(request, 'store/cart.html', {
        'products': products,
        'total': total,
    })



def checkout(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    total = sum(product.price * quantity for product, quantity in zip(products, cart.values()))

    if request.method == 'POST':
        # Create a new Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': product.name,
                        },
                        'unit_amount': int(product.price * 100),  # Amount in cents
                    },
                    'quantity': quantity,
                } for product, quantity in zip(products, cart.values())
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cart/'),
        )
        return redirect(checkout_session.url, code=303)

    return render(request, 'store/checkout.html', {'products': products, 'cart': cart, 'total': total})


def success(request):
    return render(request, 'store/success.html')

def cancel(request):
    return render(request, 'store/cancel.html')

def remove_from_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get('cart', {})
        
        if product_id in cart:
            del cart[product_id]  # Remove the item from the cart
        
        request.session['cart'] = cart
        request.session.modified = True  # Mark session as modified

        # Get the referring URL from the HTTP header
        referer = request.META.get('HTTP_REFERER', '/')
        
        # Redirect back to the page that triggered the request
        return HttpResponseRedirect(referer)

