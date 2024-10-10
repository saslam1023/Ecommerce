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
            // Get elements and values for total, price, and quantity
            let totalElement = document.getElementById('total-' + productId);  // Get the element, not the textContent
            let price = parseFloat(document.getElementById('price-' + productId).textContent) || 0;
            let quantityElement = document.getElementById('quantity-' + productId);
            let currentQuantity = parseInt(quantityElement.textContent) || 0;
            
            // Update the quantity in the UI
            quantityElement.textContent = response.quantity;
            
            // Get the cart count and total price
            let cartCount = parseInt(document.getElementById('cart-count').textContent) || 0;
            let total = parseFloat(totalElement.textContent) || 0;
        
            console.log(`BEFORE CHANGE price: ${price}, total: ${total}, currentQuantity: ${currentQuantity}`);
        
            // Adjust cartCount and total price based on response.quantity
            if (response.quantity < currentQuantity) {
                // Decrease cart count and total if response quantity is less
                cartCount -= 1;
                total -= price;  // Decrease total
                console.log(`Decreasing: price = ${price}, total = ${total}`);
            } else if (response.quantity > currentQuantity) {
                // Increase cart count and total if response quantity is more
                cartCount += 1;
                total += price;  // Increase total
                console.log(`Increasing: price = ${price}, total = ${total}`);
            }
    
            // Update the cart count in the UI
            document.getElementById('cart-count').textContent = `${cartCount}`;
            
            // Update the total in the UI (with two decimal places)
            totalElement.textContent = total.toFixed(2);  // Ensure total is displayed with two decimal places
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
