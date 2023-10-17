import logging
import argparse
import os
import sys

from common.schemas import ShopSchema, DeliverySchema, OrderDeliverySchema
from actions.inventory_monitoring import InventoryMonitor
from libs.address import get_address
from libs.notifications import (
    DingTalkNotification,
    NotificationBase,
    BarkNotification,
    FeishuNotification,
)
from libs.payments import get_payments
from libs.products import get_products


def get_notification_providers() -> list[NotificationBase]:
    providers = []
    dingtalk_token = os.environ.get("DINGTALK_TOKEN")
    bark_host = os.environ.get("BARK_HOST")
    bark_token = os.environ.get("BARK_TOKEN")
    feishu_token = os.environ.get("FEISHU_TOKEN")

    if dingtalk_token:
        providers.append(DingTalkNotification(dingtalk_token))
    if bark_token:
        providers.append(BarkNotification(bark_token, host=bark_host))
    if feishu_token:
        providers.append(FeishuNotification(feishu_token))
    return providers


def get_delivery_data() -> DeliverySchema:
    data = OrderDeliverySchema(
        first_name=os.environ.get("DELIVERY_FIRST_NAME"),
        last_name=os.environ.get("DELIVERY_LAST_NAME"),
        email=os.environ.get("DELIVERY_EMAIL"),
        phone=os.environ.get("DELIVERY_PHONE"),
        idcard=os.environ.get("DELIVERY_IDCARD"),
        payment=os.environ.get("DELIVERY_PAYMENT"),
        payment_number=int(os.environ.get("DELIVERY_PAYMENT_NUMBER") or 0),
    )
    assert (
        data.first_name
        and data.last_name
        and data.email
        and data.phone
        and data.idcard
        and data.payment
    ), "Please check the delivery information"
    return data


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--products", nargs="+", default=[], type=str, help="")
    parser.add_argument("-l", "--location", type=str, default="", help="")
    parser.add_argument("-pc", "--postal-code", type=str, default="", help="")
    parser.add_argument("--state", type=str, default="", help="")
    parser.add_argument("-lp", "--list-products", action="store_true", help="")
    parser.add_argument("-la", "--list-address", action="store_true", help="")
    parser.add_argument("-lpa", "--list-payments", action="store_true", help="")
    parser.add_argument("-o", "--order", action="store_true", help="")
    parser.add_argument("-onc", "--order-notice-count", type=int, default=1, help="")
    parser.add_argument(
        "-c", "--country", type=str, required=True, help="cn|hk-zh|sg|jp"
    )
    parser.add_argument("--code", type=str, default="", help="15|15-pro")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Query interval")
    parser.add_argument("-ft", "--filter", type=str, default="", help="")
    parser.add_argument(
        "-sft", "--store-filter", nargs="+", type=str, default=[], help=""
    )
    parser.add_argument("--ac-type", type=str, default="", help="iphone14|iphone14promax|iphone14plus")
    parser.add_argument("--ac-product", type=str, default="", help="SJTU2CH/A|SJTP2CH/A|SJTW2CH/A|SJTR2CH/A")
    return parser.parse_args()


def main():
    args = get_args()

    if args.list_products:
        assert args.country and args.code, "Lack of key information"
        products = get_products(args.code, args.country)
        for product in products:
            logging.info(product.intro())
        sys.exit(0)
    if args.list_address:
        assert args.country, "Lack of key information"
        addresses = get_address(args.country, args.filter)
        for address in addresses:
            logging.info(address)
        sys.exit(0)
    if args.list_payments:
        assert args.country, "Lack of key information"
        payments = get_payments(args.country)
        for payment in payments:
            logging.info(payment.intro())
        sys.exit(0)
    delivery_data = None
    if args.order:
        delivery_data = get_delivery_data()
        assert args.code, "Lack of key information"

    shop_data = ShopSchema(
        args.country,
        models=args.products,
        location=args.location,
        postal_code=args.postal_code,
        state=args.state,
        code=args.code,
        store_filters=args.store_filter
    )
    InventoryMonitor().start(
        shop_data,
        order=args.order,
        delivery_data=delivery_data,
        notification_providers=get_notification_providers(),
        interval=args.interval,
        order_notice_count=args.order_notice_count,
        ac_model=args.ac_product,
        ac_type=args.ac_type
    )


if __name__ == "__main__":
    main()
