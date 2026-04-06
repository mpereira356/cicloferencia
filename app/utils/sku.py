def generate_product_sku(product):
    if product.is_bike:
        prefix = "BIK"
    elif product.is_parts:
        prefix = "PEC"
    elif product.is_accessory:
        prefix = "ACE"
    else:
        prefix = "PRD"
    return f"{prefix}-{(product.id or 0):06d}"


def generate_sale_number(sale):
    return f"VEN-{(sale.id or 0):06d}"
