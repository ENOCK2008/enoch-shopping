import yaml
from django.conf import settings

def load_yaml_data():
    """Load data from a YAML file specified in settings."""
    yaml_file_path = settings.YAML_FILE_PATH

    # Open and load the YAML file
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"YAML file not found at: {yaml_file_path}")
        return None
    except yaml.YAMLError as exc:
        print(f"Error while parsing YAML: {exc}")
        return None

def calculate_total(cart_items) -> float:
    """Calculate the total amount based on the cart items.

    Args:
        cart_items (list): A list of dictionaries representing the cart items. 
                           Each dictionary must contain 'price' and 'quantity' keys.

    Returns:
        float: The total amount calculated from the cart items.
    """
    total = 0.0
    for item in cart_items:
        price = item.get('price', 0)  # Get price, default to 0 if not found
        quantity = item.get('quantity', 1)  # Default to 1 if not specified
        total += price * quantity  # Calculate total for this item
    return total
from datetime import datetime, timedelta

def calculate_delivery_date(days=7) -> str:
    """Calculate the estimated delivery date based on the current date.

    Args:
        days (int): Number of days to add to the current date to estimate delivery.

    Returns:
        str: Estimated delivery date in YYYY-MM-DD format.
    """
    estimated_date = datetime.now() + timedelta(days=days)
    return estimated_date.strftime('%Y-%m-%d')
