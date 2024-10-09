from django.shortcuts import render, redirect
from .models import Product
from django.contrib.sessions.models import Session
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('product_list')

def cart(request):
    cart = request.session.get('cart', {})
    products = []  # A list to hold product instances
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        products.append({'product': product, 'quantity': quantity})
        total += product.price * quantity

    return render(request, 'store/cart.html', {'products': products, 'total': total})

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
                        'currency': 'usd',
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
