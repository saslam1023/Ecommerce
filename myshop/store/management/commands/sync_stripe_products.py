import stripe
from django.core.management.base import BaseCommand
from store.models import Product, Category
from django.conf import settings

# Set your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Sync from Stripe to Django
        stripe_products = stripe.Product.list(limit=100)  # Fetch products from Stripe

        for stripe_product in stripe_products['data']:
            # Assume you have a default category
            default_category = Category.objects.get_or_create(name="Default Category")[0]
            
            
            product, created = Product.objects.update_or_create(
                stripe_product_id=stripe_product['id'],
                defaults={
                    'name': stripe_product['name'],
                    'price': stripe.Price.retrieve(stripe_product['default_price'])['unit_amount'] / 100,  # Stripe price is in cents
                    'category': default_category,
                    'stripe_price_id': stripe_product['default_price'],
                }
            )

        # Sync from Django to Stripe (upload new Django products to Stripe)
        unsynced_products = Product.objects.filter(stripe_product_id__isnull=True)  # Products without a stripe_product_id
        
        for product in unsynced_products:
            stripe_product = stripe.Product.create(
                name=product.name,
                description="Product from Django",  # Optional, customize as needed
            )
            
            # Create a price on Stripe (assuming you want to set a price too)
            stripe_price = stripe.Price.create(
                unit_amount=int(product.price * 100),  # Stripe expects price in cents
                currency="gbp",  # Adjust to your currency
                product=stripe_product.id,
            )
            
            # Update the product with Stripe IDs
            product.stripe_product_id = stripe_product.id
            product.stripe_price_id = stripe_price.id
            product.save()

        # Optionally, update existing products in Stripe if they have been modified in Django
        synced_products = Product.objects.exclude(stripe_product_id__isnull=True)

        for product in synced_products:
            stripe_product = stripe.Product.retrieve(product.stripe_product_id)
            if stripe_product.name != product.name:  # Example condition to update the name
                stripe.Product.modify(
                    product.stripe_product_id,
                    name=product.name,
                )

            # Update price if it has changed
            stripe_price = stripe.Price.retrieve(product.stripe_price_id)
            if stripe_price.unit_amount != int(product.price * 100):
                # Create a new price, as Stripe doesn't allow updating existing prices
                new_price = stripe.Price.create(
                    unit_amount=int(product.price * 100),
                    currency="usd",
                    product=product.stripe_product_id,
                )
                product.stripe_price_id = new_price.id
                product.save()