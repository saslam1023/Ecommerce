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