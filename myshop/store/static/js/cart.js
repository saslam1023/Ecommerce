function addToCart(productId) {
    $.ajax({
        url: "{% url 'add_to_cart' %}",  // Your Django URL for the add_to_cart view
        type: "POST",
        data: {
            product_id: productId,
            csrfmiddlewaretoken: '{{ csrf_token }}'
        },
        success: function(response) {
            // Update cart count in the UI
            $('#cart-count').text(response.cart_count);

            // Display messages
            var messages = response.messages;
            if (messages.length > 0) {
                var messageContainer = $('#message-container');
                messageContainer.empty();  // Clear previous messages

                messages.forEach(function(message) {
                    var messageHtml = '<div class="alert alert-' + message.level + '">' + message.message + '</div>';
                    messageContainer.append(messageHtml);
                });
            }
        }
    });
}







document.addEventListener('DOMContentLoaded', function() {
    // Increase product quantity
    document.querySelectorAll('.btn-increase').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            updateCartQuantity(productId, 'increase');
        });
    });

// Decrease product quantity
document.querySelectorAll('.btn-decrease').forEach(button => {
    button.addEventListener('click', function() {
        const productId = this.dataset.productId;
        const quantityElement = document.getElementById('quantity-' + productId);
        const currentQuantity = parseInt(quantityElement.textContent) || 0;

        // Check if quantity is 1, meaning it would become 0 if decreased
        if (currentQuantity === 1) {
            // Trigger confirmation if decreasing to 0
            const confirmRemove = confirm('Are you sure you want to remove this item from the cart?');
            if (confirmRemove) {
                removeFromCart(productId);  // If confirmed, remove the product
            }
        } else {
            // Otherwise, decrease the quantity normally
            updateCartQuantity(productId, 'decrease');
        }
    });
});
});

// Function to update cart quantity
function updateCartQuantity(productId, action) {
    const url = `/cart/update_quantity/`;  // Adjust URL as necessary
    const data = { product_id: productId, action: action };

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')  // Use function to get CSRF token
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(response => {
        if (response.success) {
            // Get elements and values for total, price, and quantity
            let totalElement = document.getElementById('total-' + productId);  
            let price = parseFloat(document.getElementById('price-' + productId).textContent) || 0;
            let quantityElement = document.getElementById('quantity-' + productId);
            let currentQuantity = parseInt(quantityElement.textContent) || 0;
            let totalPrice = document.getElementById('total-price');  

            
            // Update the quantity in the UI
            quantityElement.textContent = response.quantity;
            
            // Get the cart count and total price
            let cartCount = parseInt(document.getElementById('cart-count').textContent) || 0;
            let total = parseFloat(totalElement.textContent) || 0;
            let cartTotal = parseFloat(totalPrice.textContent) || 0;
        

            // Adjust cartCount and total price based on response.quantity
            if (response.quantity < currentQuantity) {
                // Decrease cart count and total if response quantity is less
                cartCount -= 1;
                total -= price;  // Decrease total
                cartTotal = cartTotal - price;
    

            } else if (response.quantity > currentQuantity) {
                // Increase cart count and total if response quantity is more
                cartCount += 1;
                total += price;  // Increase total
                cartTotal = cartTotal + price;

            }
    
            // Update the cart count in the UI
            document.getElementById('cart-count').textContent = `${cartCount}`;
            
            // Update the total in the UI (with two decimal places)
            totalElement.textContent = total.toFixed(2);  // Ensure total is displayed with two decimal places

            // Update the cart total in the UI (with two decimal places)
            totalPrice.textContent = cartTotal.toFixed(2);  // Ensure total is displayed with two decimal places

        }
    })
    .catch(error => console.error('Fetch error:', error));
}    


// Function to remove product from cart
function removeFromCart(productId) {
    const url = `/cart/remove/${productId}/`;  // Adjust URL for remove endpoint

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')  // Use function to get CSRF token
        }
    })
    .then(() => {
        // Optionally, refresh the page or remove the item from the UI
        location.reload();  // Reload the page after removal
    })
    .catch(error => console.error('Fetch error:', error));
}

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Removal modals
document.addEventListener('DOMContentLoaded', function() {



    // Handle Remove button click
    document.querySelectorAll('.remove-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();  // Prevent form submission
            const form = this.closest('form');  // Get the form to submit later
            showModal(form);
        });
    });

    // Show modal and handle confirmation
    function showModal(form) {
        const modal = document.getElementById('confirmModal');
        modal.classList.remove('hidden');
        modal.classList.add('visible');  // Show the modal

        // Handle the "Yes, Remove" button click
        document.getElementById('confirmRemove').addEventListener('click', function() {
            form.submit();  // Submit the form to remove the item
            hideModal();
        });

        // Handle the "Cancel" button click
        document.getElementById('cancelRemove').addEventListener('click', function() {
            hideModal();  // Hide the modal if cancelled
        });
    }

    function hideModal() {
        const modal = document.getElementById('confirmModal');
        modal.classList.remove('visible');
        modal.classList.add('hidden');  // Hide the modal
    }
});
