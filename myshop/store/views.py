from django.shortcuts import render, redirect
from .models import Product
from django.contrib.sessions.models import Session
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib import messages
import json
from django.urls import reverse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from dotenv import load_dotenv
import os

load_dotenv()

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
BRAND = os.getenv('BRAND')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')



stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.public_key = settings.STRIPE_PUBLIC_KEY
branding = settings.BRAND
emailSender = settings.DEFAULT_FROM_EMAIL



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
    cart_count = sum(cart.values())

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            products.append({
                'product': product,
                'quantity': quantity,
                'total': product.price * quantity # total price of each item
            })
            total += product.price * quantity
        except Product.DoesNotExist:
            pass

    return render(request, 'store/cart.html', {
        'products': products,
        'total': total,
        'total_items': cart_count
    })


def checkout(request):
    """Create a Stripe checkout session."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        products = Product.objects.filter(id__in=cart.keys())
        total = sum(product.price * quantity for product, quantity in zip(products, cart.values()))

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': product.name,
                        },
                        'unit_amount': int(product.price * 100), 
                    },
                    'quantity': quantity,
                } for product, quantity in zip(products, cart.values())
            ],
            mode='payment',
            billing_address_collection='required',
            shipping_address_collection={
                'allowed_countries': ['GB', 'US', 'CA']
            },
            success_url='http://127.0.0.1:8000/success?session_id={CHECKOUT_SESSION_ID}',
            
            cancel_url='http://127.0.0.1:8000/cancel',
        )
        return redirect(session.url, code=303)

    return render(request, 'store/checkout.html', {'products': products, 'cart': cart, 'total': total})


def xxsuccess(request):
    """Handle successful payment and send confirmation email."""
    session_id = request.GET.get('session_id')

    try:
        stripe.Account.retrieve()
        print("Successfully connected to Stripe!")
        print(session_id)
    except Exception as e:
        print(f"Error connecting to Stripe: {e}")
        print(session_id)

    if not session_id:
        return HttpResponseBadRequest('Session ID is required')

    try:
        # Retrieve the session details
        session = stripe.checkout.Session.retrieve(session_id)
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=10)

        customer_email = session.get('customer_details', {}).get('email', 'N/A')
        shipping_details = session.get('shipping')

        # Extract shipping details
        shipping_address = shipping_details.get('address', {}) if shipping_details else {}
        address_line1 = shipping_address.get('line1', 'N/A')
        city = shipping_address.get('city', 'N/A')
        postal_code = shipping_address.get('postal_code', 'N/A')
        country = shipping_address.get('country', 'N/A')

        total_amount = sum(item.price.unit_amount * item.quantity for item in line_items.data) / 100

        # Construct order summary
        order_summary = "\n".join([f"{item.description or 'Product'} - {item.price.unit_amount / 100} {item.price.currency.upper()} x {item.quantity}" 
                                    for item in line_items.data])
        
        body = f"""
        Hello,

        Thank you for your purchase!

        Order Summary:
        {order_summary}

        Total Amount Paid: £{total_amount}

        Regards,
        Your {branding}
        """

        subject = "Your Order Confirmation"

        # Send confirmation email
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [customer_email])

    except Exception as e:
        print(f"Error processing success for session {session_id}: {e}")
        return HttpResponseBadRequest('Error processing success')

    return render(request, 'store/success.html', {
        'line_items': line_items, 
        'total_amount': total_amount, 
        'session': session,
        'customer_email': customer_email, 
        'address_line1': address_line1, 
        'city': city,
        'postal_code': postal_code, 
        'country': country
    })


""" This is a working success form 
def success(request):
    session_id = request.GET.get('session_id')

    session = stripe.checkout.Session.retrieve(session_id)
    line_items = stripe.checkout.Session.list_line_items(session_id, limit=10)

    customer_email = session.get('customer_details', {}).get('email', 'N/A')
    shipping_details = session.get('shipping')

        # Extract shipping details
    shipping_address = shipping_details.get('address', {}) if shipping_details else {}
    address_line1 = shipping_address.get('line1', 'N/A')
    city = shipping_address.get('city', 'N/A')
    postal_code = shipping_address.get('postal_code', 'N/A')
    country = shipping_address.get('country', 'N/A')

    total_amount = sum(item.price.unit_amount * item.quantity for item in line_items.data) / 100

        # Construct order summary
    order_summary = "\n".join([f"{item.description or 'Product'} - {item.price.unit_amount / 100} {item.price.currency.upper()} x {item.quantity}" 
                                    for item in line_items.data])

    #return render(request, 'store/success.html', {'id': session_id})
    return render(request, 'store/success.html', {
        'line_items': line_items, 
        'total_amount': total_amount, 
        'session': session,
        'customer_email': customer_email, 
        'address_line1': address_line1, 
        'city': city,
        'postal_code': postal_code, 
        'country': country
    })
"""


from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseBadRequest

def success(request):
    session_id = request.GET.get('session_id')

    # Check if the session ID is provided
    if not session_id:
        return HttpResponseBadRequest('Session ID is required')

    try:
        # Retrieve the session details from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=10)

        # Extract customer email
        customer_email = session.get('customer_details', {}).get('email', 'N/A')
        shipping_details = session.get('shipping')

        # Extract shipping details
        shipping_address = shipping_details.get('address', {}) if shipping_details else {}
        address_line1 = shipping_address.get('line1', 'N/A')
        city = shipping_address.get('city', 'N/A')
        postal_code = shipping_address.get('postal_code', 'N/A')
        country = shipping_address.get('country', 'N/A')

        # Calculate total amount
        total_amount = sum(item.price.unit_amount * item.quantity for item in line_items.data) / 100

        # Construct order summary
        order_summary = "\n".join([f"{item.description or 'Product'} - {item.price.unit_amount / 100} {item.price.currency.upper()} x {item.quantity}" 
                                    for item in line_items.data])

        # Prepare the email body
        body = f"""
        Hello,

        Thank you for your purchase!

        Order Summary:
        {order_summary}

        Total Amount Paid: £{total_amount:.2f}

        Shipping Address:
        {address_line1}, {city}, {postal_code}, {country}

        Regards,
        Your Brand Name
        """

        subject = "Your Order Confirmation"

        # Send confirmation email
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [customer_email])

    except Exception as e:
        print(f"Error processing success for session {session_id}: {e}")
        return HttpResponseBadRequest('Error processing success')

    # Render the success page with relevant details
    return render(request, 'store/success.html', {
        'line_items': line_items, 
        'total_amount': total_amount, 
        'session': session,
        'customer_email': customer_email, 
        'address_line1': address_line1, 
        'city': city,
        'postal_code': postal_code, 
        'country': country
    })


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


 # Use this only if you are handling CSRF tokens properly elsewhere
def update_cart_quantity(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            action = data.get('action')

            # Retrieve the cart from the session
            cart = request.session.get('cart', {})
            quantity = cart.get(product_id, 0)


            if action == 'increase':
                quantity += 1
            elif action == 'decrease':
                quantity = max(0, quantity - 1)  # Ensure it doesn't go below 0
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})

            # Update the cart in the session
            if quantity > 0:
                cart[product_id] = quantity
            else:
                cart.pop(product_id, None)  # Remove item if quantity is 0

            request.session['cart'] = cart
            request.session.modified = True  # Mark session as modified

            # Return the updated quantity
            return JsonResponse({'success': True, 'quantity': cart.get(product_id, 0)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})