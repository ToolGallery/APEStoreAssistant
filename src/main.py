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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--products", nargs="+", default=[], type=str, help="")
    parser.add_argument("-l", "--location", type=str, default="", help="")
    parser.add_argument("-pc", "--postal-code", type=str, default="", help="")
    parser.add_argument("--state", type=str, default="", help="")
    parser.add_argument("-lp", "--list-products", action="store_true", help="")
    parser.add_argument(
        "-c", "--country", type=str, required=True, help="cn|hk-zh|sg|jp"
    )
    parser.add_argument("--code", type=str, default="", help="15|15-pro")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Query interval")
    return parser.parse_args()


def main():
    args = get_args()

    if args.list_products:
        assert args.country and args.code, "Lack of key information"
        products = get_products(args.code, args.country)
        for product in products:
            logging.info(product.intro())
        sys.exit(0)

    shop_data = ShopSchema(
        args.country,
        models=args.products,
        location=args.location,
        postal_code=args.postal_code,
        state=args.state,
    )
    InventoryMonitor().start(shop_data, get_notification_providers(), interval=args.interval)


if __name__ == "__main__":
    main()
