import sys
import os
import django
from django.core.mail import send_mail
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')


# Setup Django
django.setup()

# Now you can access Django settings
DEFAULT_FROM_EMAIL = os.getenv('MAIL_DEFAULT_SENDER')

# Set the subject, body, and recipient
subject = "Test Email from Django"
body = "This is a test email to check if the email sending functionality is working."
recipient_list = ["saslam1023@icloud.com"]  # Replace with your email address

# Send the email
send_mail(subject, body, DEFAULT_FROM_EMAIL, recipient_list)

print("Test email sent!")
