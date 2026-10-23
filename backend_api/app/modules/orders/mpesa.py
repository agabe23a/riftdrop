import base64
import httpx
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
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
        if not settings.MPESA_CONSUMER_KEY or not settings.MPESA_CONSUMER_SECRET:
            raise HTTPException(status_code=503, detail="Payments are not configured")
        url = f"{MpesaService.get_base_url()}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_auth}"}

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to authenticate with M-Pesa API")
            token = response.json().get("access_token")
            if not token:
                raise HTTPException(status_code=502, detail="Payment provider returned an invalid response")
            return token

    @staticmethod
    async def trigger_stk_push(phone_number: str, amount: Decimal, order_id: int) -> dict:
        """Pushes the PIN prompt to the customer's phone."""
        token = await MpesaService.get_access_token()
        url = f"{MpesaService.get_base_url()}/mpesa/stkpush/v1/processrequest"
        
        if not all([settings.MPESA_PASSKEY, settings.MPESA_SHORTCODE, settings.MPESA_CALLBACK_URL]):
            raise HTTPException(status_code=503, detail="Payments are not configured")
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        # Format phone to Safaricom standard (e.g., 2547XXXXXXXX)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number[1:]

        # The URL Safaricom will hit when the user enters their PIN
        # (This will need to be a public IP when deployed to Render)
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"RiftDrop Order {order_id}",
            "TransactionDesc": "Payment for RiftDrop Order"
        }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="M-Pesa STK Push failed to initiate.")
            return response.json()
