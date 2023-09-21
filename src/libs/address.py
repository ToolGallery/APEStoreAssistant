import requests


def get_address(country: str, filter_str: str = ""):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    }
    filters = filter_str.split(" ")
    params = {
        "state": filters[0] if len(filters) > 0 else None,
        "city": filters[1] if len(filters) > 1 else None,
        "district": filters[2] if len(filters) > 2 else None,
    }
    resp = requests.get(
        f"https://www.apple.com/{country}/shop/address-lookup",
        params=params,
        headers=default_headers,
    )
    resp_json = resp.json()
    assert resp_json["head"]["status"] == "200"
    address_data = resp_json["body"].popitem()[1]
    if isinstance(address_data, dict):
        addresses = [i["value"] for i in address_data["data"]]
    else:
        addresses = [address_data]
    return addresses
