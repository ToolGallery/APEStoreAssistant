import json
import re

import requests

from common.schemas import ProductSchema


def get_products(code: str, country: str):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    }
    resp = requests.get(
        f"https://www.apple.com/{country}/shop/buy-iphone/iphone-{code}",
        headers=default_headers,
    )
    content = resp.text
    assert "productSelectionData" in resp.text
    return parse_products(content)


def parse_products(content):
    select_match = re.search(
        r"window.PRODUCT_SELECTION_BOOTSTRAP = (.+?)</script>", content, flags=re.DOTALL
    )
    assert select_match
    select_text = (
        select_match.group(1)
        .strip()
        .replace("productSelectionData", '"productSelectionData"')
    )
    select_data = json.loads(select_text)["productSelectionData"]
    products = []
    prices_data = select_data["displayValues"]["prices"]
    colors_data = select_data["displayValues"]["dimensionColor"]
    for product in select_data["products"]:
        price_tag = product["fullPrice"]
        price_data = prices_data[price_tag]
        products.append(
            ProductSchema(
                type=product["familyType"],
                model=product["partNumber"],
                color=product["dimensionColor"],
                capacity=product["dimensionCapacity"],
                color_display=colors_data[product["dimensionColor"]]["value"],
                price=float(price_data["currentPrice"]["raw_amount"]),
                price_display=price_data["currentPrice"]["amount"],
                price_currency=price_data["priceCurrency"],
                carrier_model=product.get("carrierModel", ""),
            )
        )
    return sorted(products, key=lambda x: (x.price, x.color))
