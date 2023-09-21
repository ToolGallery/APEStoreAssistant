import logging
import time
from enum import Enum
from typing import Optional

from libs.requests import Request
from libs.notifications import NotificationBase
from common.schemas import DeliverySchema, ShopSchema

logger = logging.getLogger(__name__)

apple_api_host = "https://www.apple.com"


class DeliveryStatusEnum(str, Enum):
    AVAILABLE = "available"
    INELIGIBLE = "ineligible"


class InventoryMonitor(object):
    def __init__(self) -> None:
        super().__init__()
        self.request = Request(apple_api_host)
        self.is_stop = False

    def start(
        self,
        shop_data: ShopSchema,
        notification_providers: Optional[list[NotificationBase]] = None,
        interval: int = 5,
    ):
        logger.info(f"Start monitoring, query interval: {interval}s")
        while not self.is_stop:
            try:
                inventory_data = self.get_data(
                    shop_data.country,
                    shop_data.models,
                    shop_data.location,
                )
                pickup_lists = self.parse_data(inventory_data)
                available_lists = [
                    i for i in pickup_lists if i.status == DeliveryStatusEnum.AVAILABLE
                ]

                for pickup in pickup_lists:
                    logger.info(pickup.intro())

                if available_lists and notification_providers:
                    self.push_notifications(available_lists, notification_providers)

            except Exception as e:
                logging.exception(
                    "Failed to retrieve inventory data with error: ", exc_info=e
                )
            time.sleep(interval)

    def push_notifications(
        self, pickup_lists: list[DeliverySchema], providers: list[NotificationBase]
    ):
        title = "Apple inventory notification"
        buffers = []
        for pickup in pickup_lists:
            buffers.append(pickup.intro())

        if not buffers:
            return

        for provider in providers:
            try:
                provider.push(
                    title,
                    "\r\n".join(buffers),
                    key=f"inventory_monitor_{provider.name}",
                    min_interval=60,
                )
            except Exception as e:
                logging.exception(
                    "Inventory information push failed with error: ", exc_info=e
                )

    def get_data(
        self,
        country: str,
        models: list[str],
        location: str = "",
        postal_code: str = "",
        state: str = "",
    ):
        parts = {f"parts.{idx}": i for idx, i in enumerate(models)}
        search_params = {
            "searchNearby": "true",
            "pl": "true",
            "mts.0": "regular",
            "mts.1": "compact",
        } | parts
        if location:
            search_params["location"] = location
        if postal_code:
            search_params["postalCode"] = postal_code
        if state:
            search_params["state"] = state

        resp = self.request.get(
            f"/{country}/shop/fulfillment-messages", params=search_params
        )

        return resp.json()

    def parse_data(self, data: dict):
        pickup_message = data["body"]["content"]["pickupMessage"]
        if not pickup_message.get("stores"):
            logger.error("No stores found")
            return []
        deliveries = []
        for store in pickup_message["stores"]:
            parts = store["partsAvailability"].values()
            for part in parts:
                address = store["retailStore"]["address"]
                model_name = part["messageTypes"]["regular"][
                    "storePickupProductTitle"
                ].replace("\xa0", " ")
                deliveries.append(
                    DeliverySchema(
                        state=address["state"],
                        city=address["city"],
                        district=address["district"],
                        store_name=store["storeName"],
                        model_name=model_name,
                        pickup_quote=part["pickupSearchQuote"],
                        model=part["partNumber"],
                        status=part["pickupDisplay"],
                        pickup_type=part["pickupType"],
                    )
                )

        return deliveries
