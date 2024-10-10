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
            updateCartQuantity(productId, 'decrease');
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
            // Update the quantity displayed in the UI
            let quantity = document.getElementById('quantity-' + productId).textContent;
            document.getElementById('quantity-' + productId).textContent = response.quantity;
            let cartCount = document.getElementById('cart-count').textContent;
            cartCount = parseInt(cartCount) || 0;
        
            // Adjust cartCount based on response.quantity
            if (response.quantity < quantity) {
                // Decrease cart count if response quantity is less
                cartCountTotal = cartCount - 1;
            } else if (response.quantity > quantity) {
                // Increase cart count if response quantity is more
                cartCountTotal = cartCount + 1;
            } else {
                // If the quantity is the same, keep it the same
                cartCountTotal = cartCount;
            }

            document.getElementById('cart-count').textContent = `${cartCountTotal}`;
        }
        
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
