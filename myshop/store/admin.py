from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_link', 'display_image')

    def name_link(self, obj):
        url = reverse('admin:store_product_change', args=[obj.id])  # Adjust 'store' to your app name
        return mark_safe(f'<a href="{url}"><strong>{obj.name}</strong></a>')
    name_link.short_description = 'Name'  # Optional: Column header in admin

    def display_image(self, obj):
        if obj.image:  # Assuming you have an 'image' field in your Product model
            return mark_safe(f'<img src="{obj.image.url}" style="width: 50px; height: auto;"/>')
        return 'No Image'
    display_image.short_description = 'Image'  # Optional: Column header in admin

admin.site.register(Product, ProductAdmin)
