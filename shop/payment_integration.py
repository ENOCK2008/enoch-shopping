import requests
from django.conf import settings

def initiate_mpesa_payment(phone_number, amount, order_id):
    url = f"{settings.MOBILE_MONEY_CONFIG['API_BASE_URL']}mpesa/initiate"
    headers = {
        'Authorization': f"Bearer {settings.MOBILE_MONEY_CONFIG['MPESA_API_KEY']}",
        'Content-Type': 'application/json'
    }
    payload = {
        'phone_number': phone_number,
        'amount': amount,
        'order_id': order_id,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def initiate_mtn_payment(phone_number, amount, order_id):
    url = f"{settings.MOBILE_MONEY_CONFIG['API_BASE_URL']}mtn/initiate"
    headers = {
        'Authorization': f"Bearer {settings.MOBILE_MONEY_CONFIG['MTN_API_KEY']}",
        'Content-Type': 'application/json'
    }
    payload = {
        'phone_number': phone_number,
        'amount': amount,
        'order_id': order_id,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def initiate_airtel_payment(phone_number, amount, order_id):
    url = f"{settings.MOBILE_MONEY_CONFIG['API_BASE_URL']}airtel/initiate"
    headers = {
        'Authorization': f"Bearer {settings.MOBILE_MONEY_CONFIG['AIRTEL_API_KEY']}",
        'Content-Type': 'application/json'
    }
    payload = {
        'phone_number': phone_number,
        'amount': amount,
        'order_id': order_id,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
