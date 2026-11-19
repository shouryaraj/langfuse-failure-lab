from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client, observe


@observe()
def parse_order(order):
    return order["quantity"]


@observe()
def validate_quantity(quantity):
    if quantity <= 0:
        raise ValueError("quantity must be > 0")


@observe()
def price_per_item(order):
    quantity = parse_order(order)
    try:
        validate_quantity(quantity)
    except ValueError:
        return None
    return order["total"] / quantity


@observe()
def main():
    order = {"id": "A-1001", "total": 50.0, "quantity": 0}
    print(price_per_item(order))


if __name__ == "__main__":
    try:
        main()
    finally:
        get_client().flush()
