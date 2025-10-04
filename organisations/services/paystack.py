from typing import Dict
import requests
from django.conf import settings


class PaystackService:
    def __init__(self):
        self.base_url = 'https://api.paystack.co'
        self.secret_key = settings.PAYSTACK_SECRET_KEY

    def _headers(self):
        return {'Authorization': f'Bearer {self.secret_key}', 'Content-Type': 'application/json'}

    def initialize_transaction(self, email: str, amount: int, reference: str, metadata: Dict = None) -> Dict:
        """
        Initialize a Paystack transaction
        Amount should be in kobo (multiply amount in Naira by 100)
        """
        url = f"{self.base_url}/transaction/initialize"
        payload = {'email': email, 'amount': amount, 'reference': reference, 'metadata': metadata or {}}

        response = requests.post(url, json=payload, headers=self._headers())
        return response.json()

    def verify_transaction(self, reference: str) -> Dict:
        """Verify a Paystack transaction"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self._headers())
        return response.json()

    def create_subscription(self, email: str, plan_code: str) -> Dict:
        """Create a subscription for a customer"""
        url = f"{self.base_url}/subscription"
        payload = {'customer': email, 'plan': plan_code}
        response = requests.post(url, json=payload, headers=self._headers())
        return response.json()

    def cancel_subscription(self, subscription_code: str) -> Dict:
        """Cancel a subscription"""
        url = f"{self.base_url}/subscription/{subscription_code}/disable"
        response = requests.post(url, headers=self._headers())
        return response.json()
