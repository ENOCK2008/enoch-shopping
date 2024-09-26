# shop/mtn_service.py

import requests

def get_api_user_info(api_user_id, subscription_key):
    BASE_URL = 'https://momodeveloper.mtn.com/apiuser/'
    url = f"{BASE_URL}{api_user_id}"

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses

        return response.json()  # Return the response JSON

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")

    return None  # Return None if there was an error
