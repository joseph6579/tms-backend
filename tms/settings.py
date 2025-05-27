# Add to existing settings.py

# Paystack Settings
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', cast=str)
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', cast=str)