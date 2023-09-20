import logging
import argparse
import os
import sys

from common.schemas import ShopSchema
from actions.inventory_monitoring import InventoryMonitor
from libs.notifications import DingTalkNotification, NotificationBase, BarkNotification
from libs.products import get_products


def get_notification_providers() -> list[NotificationBase]:
    providers = []
    dingtalk_token = os.environ.get("DINGTALK_TOKEN")
    bark_host = os.environ.get("BARK_HOST")
    bark_token = os.environ.get("BARK_TOKEN")
    if dingtalk_token:
        providers.append(DingTalkNotification(dingtalk_token))
    if bark_token:
        providers.append(BarkNotification(bark_token, host=bark_host))
    return providers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--products", nargs="+", default=[], type=str, help="")
    parser.add_argument("-l", "--location", type=str, default="", help="")
    parser.add_argument("--list-products", action="store_true", help="")
    parser.add_argument("-c", "--country", type=str, required=True, help="cn|hk-zh|sg|jp")
    parser.add_argument("--code", type=str, default="", help="15|15-pro")
    args = parser.parse_args()

    if args.list_products:
        assert args.country and args.code, "Lack of key information"
        products = get_products(args.code, args.country)
        for product in products:
            logging.info(product.intro())
        sys.exit(0)

    shop_data = ShopSchema(args.country, models=args.products, location=args.location)
    InventoryMonitor().start(shop_data, get_notification_providers(), interval=5)


if __name__ == "__main__":
    main()
