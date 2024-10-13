// Initialize Stripe
const stripe = Stripe("pk_test_51Pgu9iRsaAPRmc2jsZT5oY0fdQL7vLS8elANtE66i9X937LZrUmmGSGpRF2ojjlIU9Jh6lQ0D9PTd6KJmM9vo1Fw001zv4h6vM"); 
const elements = stripe.elements();

// Create an instance of the card Element
const cardElement = elements.create('card');
cardElement.mount('#card-element');

// Handle real-time validation errors on the card element
cardElement.on('change', function(event) {
    const displayError = document.getElementById('card-errors');
    if (event.error) {
        displayError.textContent = event.error.message;
    } else {
        displayError.textContent = '';
    }
});

// Handle form submission
const form = document.getElementById('payment-form');
form.addEventListener('submit', function(event) {
    event.preventDefault();

    // Collect shipping info
    const shippingInfo = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        address: {
            line1: document.getElementById('address').value,
            city: document.getElementById('city').value,
            state: document.getElementById('county').value, // This could also be left out if not needed
            postal_code: document.getElementById('postcode').value,
            country: document.getElementById('country').value,
        }
    };
    

    // Create the payment method
    stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
            email: document.getElementById('email').value,
            country: 'GB',

        }
    }).then(function(result) {
        if (result.error) {
            // Show error in payment form
            const errorElement = document.getElementById('card-errors');
            errorElement.textContent = result.error.message;
        } else {
            // Send payment method and shipping info to your server for payment intent creation
            processPayment(result.paymentMethod.id, shippingInfo);
        }
    });
});

// Function to send payment method and shipping info to server
function processPayment(paymentMethodId, shippingInfo) {
    fetch("/create_payment", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            paymentMethodId: paymentMethodId,
            name: shippingInfo.name,
            email: shippingInfo.email,
            address: shippingInfo.address.line1,
            city: shippingInfo.address.city,
            // Change 'county' to 'state' or remove if not needed
            state: shippingInfo.address.state, 
            postcode: shippingInfo.address.postal_code,
            country: shippingInfo.address.country,
        })
    })
    
    .then(function(response) {
        return response.json();
    })
    .then(function(responseJson) {
        if (responseJson.error) {
            console.error(responseJson.error);
        } else if (responseJson.requires_action) {
            // Handle 3D Secure (if required)
            stripe.handleCardAction(responseJson.payment_intent_client_secret).then(function(result) {
                if (result.error) {
                    // Show error in payment form
                    document.getElementById('card-errors').textContent = result.error.message;
                } else {
                    // 3D Secure complete, confirm payment
                    finalizePayment(result.paymentIntent.id, shippingInfo);
                }
            });
        } else {
            // Payment succeeded, redirect to success page
            window.location.href = "/success";
        }
    });
}

// Function to handle the final confirmation of payment after 3D Secure
function finalizePayment(paymentIntentId, shippingInfo) {
    fetch("/finalize_payment", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            paymentIntentId: paymentIntentId
        })
    }).then(function(response) {
        return response.json();
    }).then(function(responseJson) {
        if (responseJson.error) {
            console.error("Payment failed:", responseJson.error);
        } else {
            // Payment succeeded, redirect to success page
            window.location.href = "/success";
        }
    });
}
