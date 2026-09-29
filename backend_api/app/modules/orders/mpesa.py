import base64
import httpx
from datetime import datetime
from fastapi import HTTPException
from app.core.config import settings

class MpesaService:
    @staticmethod
    def get_base_url():
        if settings.MPESA_ENVIRONMENT == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    @staticmethod
    async def get_access_token() -> str:
        """Authenticates with Safaricom to get a temporary bearer token."""
        url = f"{MpesaService.get_base_url()}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_auth}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to authenticate with M-Pesa API")
            return response.json().get("access_token")

    @staticmethod
    async def trigger_stk_push(phone_number: str, amount: float, order_id: int) -> dict:
        """Pushes the PIN prompt to the customer's phone."""
        token = await MpesaService.get_access_token()
        url = f"{MpesaService.get_base_url()}/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        # Format phone to Safaricom standard (e.g., 2547XXXXXXXX)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number[1:]

        # The URL Safaricom will hit when the user enters their PIN
        # (This will need to be a public IP when deployed to Render)
        callback_url = "https://your-production-url.onrender.com/api/v1/orders/mpesa-callback"

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount), # Daraja only accepts integers
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": f"RiftDrop Order {order_id}",
            "TransactionDesc": "Payment for RiftDrop Order"
        }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="M-Pesa STK Push failed to initiate.")
            return response.json()