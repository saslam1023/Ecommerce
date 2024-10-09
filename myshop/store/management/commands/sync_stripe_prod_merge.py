import os
import requests
import stripe
from django.core.management.base import BaseCommand
from store.models import Product, Category
from django.conf import settings

# Set your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Ensure the products directory exists
        products_directory = os.path.join(settings.MEDIA_ROOT, 'products')
        if not os.path.exists(products_directory):
            os.makedirs(products_directory)

        # Sync from Stripe to Django
        stripe_products = stripe.Product.list(limit=100)  # Fetch products from Stripe

        # Create a set of active Stripe product IDs
        active_stripe_product_ids = {product['id'] for product in stripe_products['data']}

        for stripe_product in stripe_products['data']:
            # Assume you have a default category
            default_category, _ = Category.objects.get_or_create(name="Default Category")

            # Download image if it exists
            image_path = None
            if stripe_product['images']:
                image_url = stripe_product['images'][0]  # Get the first image URL

                # Download the image only if it doesn't already exist in the Django database
                image_name = os.path.basename(image_url)  # Extract the file name from URL
                existing_product = Product.objects.filter(stripe_product_id=stripe_product['id']).first()

                # Check if the product already has an image
                if existing_product and existing_product.image:
                    # If image exists and matches the Stripe image, skip downloading
                    if existing_product.image.name == f'products/{image_name}':
                        image_path = existing_product.image.name
                    else:
                        # Download the image and save it
                        image_response = requests.get(image_url)
                        if image_response.status_code == 200:
                            image_path = os.path.join('products', image_name)

                            # Save the image to the media directory
                            with open(os.path.join(products_directory, image_name), 'wb') as img_file:
                                img_file.write(image_response.content)
                        else:
                            self.stdout.write(self.style.WARNING(f'Failed to download image for product {stripe_product["name"]}'))
                else:
                    # Download the image since it doesn't exist in Django
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image_path = os.path.join('products', image_name)

                        # Save the image to the media directory
                        with open(os.path.join(products_directory, image_name), 'wb') as img_file:
                            img_file.write(image_response.content)
                    else:
                        self.stdout.write(self.style.WARNING(f'Failed to download image for product {stripe_product["name"]}'))

            # Get the default price safely
            default_price_id = stripe_product.get('default_price')
            if default_price_id is not None:
                try:
                    stripe_price = stripe.Price.retrieve(default_price_id)
                    price_amount = stripe_price['unit_amount'] / 100  # Stripe price is in cents
                except stripe.error.InvalidRequestError:
                    self.stdout.write(self.style.WARNING(f'Invalid price ID for product {stripe_product["name"]}'))
                    price_amount = 0.0  # Set to zero or handle as needed
            else:
                self.stdout.write(self.style.WARNING(f'No default price for product {stripe_product["name"]}'))
                price_amount = 0.0  # Set to zero or handle as needed

            # Create or update the product in Django
            product, created = Product.objects.update_or_create(
                stripe_product_id=stripe_product['id'],
                defaults={
                    'name': stripe_product['name'],
                    'price': price_amount,
                    'category': default_category,
                    'stripe_price_id': default_price_id,
                    'image': image_path,  # Save the image path
                    'is_active': True  # Set product as active
                }
            )

        # Deactivate products in Django that are no longer in Stripe
        Product.objects.exclude(stripe_product_id__in=active_stripe_product_ids).update(is_active=False)

        # Sync from Django to Stripe (upload new Django products to Stripe)
        unsynced_products = Product.objects.filter(stripe_product_id__isnull=True)  # Products without a stripe_product_id

        for product in unsynced_products:
            # Prepare product creation parameters
            stripe_product_params = {
                'name': product.name,
                'description': product.description, 
                'images': [f"file_{stripe_file.id}"], 
            }

            # Upload the image to Stripe if it exists

        if product.image:
            with open(product.image.path, 'rb') as img_file:
                # Upload the image file to Stripe
                stripe_file = stripe.File.create(
                    purpose='product_image',
                    file=img_file,
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully uploaded image to Stripe: {stripe_file.id}'))

            # Append the file ID to the images list
                stripe_product_params['images'].append(f"file_{stripe_file.id}")  

            try:
                # Create the product on Stripe with the prepared parameters
                stripe_product = stripe.Product.create(**stripe_product_params)
                self.stdout.write(self.style.SUCCESS(f'Successfully created product on Stripe: {stripe_product.id}'))


                
                # Create a price on Stripe (assuming you want to set a price too)
                stripe_price = stripe.Price.create(
                unit_amount=int(product.price * 100),  # Stripe expects price in cents
                currency="gbp",  # Adjust to your currency
                product=stripe_product.id,
                )
                
                # Update the product with Stripe IDs
                product.stripe_product_id = stripe_product.id
                product.stripe_price_id = stripe_price.id

                        # Update your product to reflect that it's synced
                product.is_synced = True
                product.save()
            except stripe.error.InvalidRequestError as e:
                print(f"Error creating product for {product.name}: {e.user_message}")
        else:
            print(f"No image available for product: {product.name}")
    
        # Optionally, update existing products in Stripe if they have been modified in Django
        synced_products = Product.objects.exclude(stripe_product_id__isnull=True)

        for product in synced_products:
            stripe_product = stripe.Product.retrieve(product.stripe_product_id)
            
            # Update name if it has changed
            if stripe_product.name != product.name:
                stripe.Product.modify(
                    product.stripe_product_id,
                    name=product.name,
                )

            # Update price if it has changed
            if product.stripe_price_id:
                stripe_price = stripe.Price.retrieve(product.stripe_price_id)
                if stripe_price.unit_amount != int(product.price * 100):
                    # Create a new price, as Stripe doesn't allow updating existing prices
                    new_price = stripe.Price.create(
                        unit_amount=int(product.price * 100),
                        currency="gbp",
                        product=product.stripe_product_id,
                    )
                    product.stripe_price_id = new_price.id
                    product.save()
