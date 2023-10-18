import dataclasses
import json
import logging
import random
import re
import threading
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, parse_qsl, quote_plus

from common.schemas import OrderSchema
from libs.requests import Request

apple_api_host = "https://www.apple.com"

logger = logging.getLogger(__name__)


class Order(object):
    def __init__(self, country: str) -> None:
        super().__init__()
        # only support cn yet
        assert country == "cn", "Only support cn yet"
        api_host = apple_api_host + ".cn"
        self.session = Request(
            api_host,
            headers={
                "Referer": f"https://www.apple.com/{country}/shop/bag",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        self.secure_host = ""

    def init_order(self, order_data: OrderSchema):
        self.add_to_cart(order_data.model, order_data.model_code, order_data.ac_type, order_data.ac_model)
        cart_item_id = self.get_cart_item_id()

        signin_url, signin_params, secure_api_host = self.start_checkout(
            cart_item_id,
            order_data.country,
            order_data.state,
            order_data.city,
            order_data.district,
        )
        self.secure_host = secure_api_host

        self.get_page_with_meta(signin_url, None)

        signin_data = self.signin(signin_params)

        logger.debug("Access '/bg' page")
        self.get_page_with_meta(signin_data["head"]["data"]["url"], None)

        self.update_delivery_method()

    def start_order(self, order_data: OrderSchema):
        logger.info(
            f"Order starting with {order_data.model_code} {order_data.model} {order_data.state} {order_data.city}..."
        )

        address_data = self.fill_address(
            order_data.store_number,
            order_data.country,
            order_data.state,
            order_data.city,
            order_data.district,
        )

        selected_window = self.get_select_window(address_data)
        if not selected_window:
            return False

        self.fill_contact(
            selected_window,
            order_data.store_number,
            order_data.country,
            order_data.state,
            order_data.city,
            order_data.district,
        )

        self.fill_recipient(
            order_data.delivery.first_name,
            order_data.delivery.last_name,
            order_data.delivery.email,
            order_data.delivery.phone,
            order_data.delivery.idcard,
        )
        self.fill_pay_method(
            order_data.delivery.payment, order_data.delivery.payment_number
        )
        self.finish_checkout()

        return True

    def get_cart_item_id(self):
        logger.info("Getting cart id...")
        page_data = self.get_page_with_meta("/shop/bag", None)
        item_id = page_data["shoppingCart"]["items"]["c"].pop()
        logger.debug(f"Cart item id: {item_id}")
        return item_id

    def add_to_cart(self, model_number: str, phone_model: str, ac_type: str, ac_model: str):
        logger.info("Adding to cart...")
        resp_atb = self.session.get("/shop/beacon/atb")
        atb_str: str = resp_atb.cookies.get("as_atb")
        atb_token = atb_str.split("|")[-1]

        params = {
            "product": model_number,
            "purchaseOption": "fullPrice",
            "step": "select",
            "ams": "0",
            "atbtoken": atb_token,
            "igt": "true",
            "add-to-cart": "add-to-cart",
        }

        if ac_type:
            key = "ao.add_" + ac_type +"_ac_iup"
            params[key] = ac_model

        resp = self.session.get(
            f"/shop/buy-iphone/iphone-{phone_model}/{model_number}#",
            params=params,
        )
        assert resp.status_code == 200

    def start_checkout(
        self, item_id: str, country: str, state: str, city: str, district: str
    ) -> (dict, str):
        logger.info("Starting checkout...")
        data = {
            "shoppingCart.recommendations.recommendedItem.part": "",
            f"shoppingCart.items.{item_id}.isIntentToGift": "false",
            f"shoppingCart.items.{item_id}.itemQuantity.quantity": "1",
            f"shoppingCart.items.{item_id}.delivery.lineDeliveryOptions.address.provinceCityDistrictTabs.city": city,
            f"shoppingCart.items.{item_id}.delivery.lineDeliveryOptions.address.provinceCityDistrictTabs.state": state,
            f"shoppingCart.items.{item_id}.delivery.lineDeliveryOptions.address.provinceCityDistrictTabs.provinceCityDistrict": f"{state} {city} {district}",
            f"shoppingCart.items.{item_id}.delivery.lineDeliveryOptions.address.provinceCityDistrictTabs.countryCode": country,
            f"shoppingCart.items.{item_id}.delivery.lineDeliveryOptions.address.provinceCityDistrictTabs.district": district,
            "shoppingCart.locationConsent.locationConsent": "false",
            "shoppingCart.summary.promoCode.promoCode": "",
            "shoppingCart.actions.fcscounter": "",
            "shoppingCart.actions.fcsdata": "",
        }
        resp = self.session.post(
            "/shop/bagx/checkout_now",
            params={
                "_a": "checkout",
                "_m": "shoppingCart.actions",
            },
            data=data,
        )
        resp_json = resp.json()
        signin_url = resp_json["head"]["data"]["url"]
        url_parsed = urlparse(signin_url)

        signin_params = dict(parse_qsl(url_parsed.query))
        secure_api_host = f"{url_parsed.scheme}://{url_parsed.hostname}"

        logger.debug(f"Secure api host: {secure_api_host}")
        return signin_url, signin_params, secure_api_host

    def signin(self, signin_params: dict):
        timestamp = str(int(time.time() * 1000))
        now = datetime.now()
        data = {
            "signIn.consentOverlay.policiesAccepted": "true",
            "signIn.consentOverlay.dataHandleByApple": "true",
            "signIn.consentOverlay.dataOutSideMyCountry": "true",
            "signIn.guestLogin.deviceID": f'TF1;015;;;;;;;;;;;;;;;;;;;;;;Mozilla;Netscape;5.0 (Macintosh);20100101;undefined;true;Intel Mac OS X 10.15;true;MacIntel;undefined;Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{random.randrange(100, 109)}.0) Gecko/20100101 Firefox/{random.randrange(100, 117)}.0;en-US;undefined;secure7.www.apple.com.cn;undefined;undefined;undefined;undefined;false;false;{timestamp};8;6/7/2005, 9:33:44 PM;2560;1440;;;;;;;;-480;-480;{now.strftime("%-m/%-d/%Y")}, {now.strftime("%-I:%M:%S %p")};30;2560;1415;0;25;;;;;;;;;;;;;;;;;;;25;',
        }
        data["signIn.guestLogin.deviceID"] = ";".join(
            [quote_plus(i) for i in data["signIn.guestLogin.deviceID"].split(";")]
        )

        sign_resp = self.session.post(
            self.secure_host + "/shop/signInx",
            params=signin_params | {"_a": "guestLogin", "_m": "signIn.guestLogin"},
            data=data,
        )
        sign_resp_json = sign_resp.json()
        start_response = self.session.post(
            sign_resp_json["head"]["data"]["url"],
            data=sign_resp_json["head"]["data"]["args"],
        )
        start_response_json = start_response.json()
        assert start_response_json["head"]["status"] == 302
        return start_response_json

    def checkout_request(
        self,
        url: str,
        params: Optional[dict],
        data: Optional[dict] = None,
        assert_code: int = 200,
    ):
        resp = self.session.post(url, params=params, data=data)

        resp_json = resp.json()
        if assert_code:
            logger.debug(f"Url {url} response {resp_json}")
            resp_status = resp_json["head"]["status"]
            if resp_status != assert_code:
                return False
            assert (
                resp_status == assert_code
            ), f"Expected {assert_code}, actually {resp_status}"

        return resp_json

    def update_delivery_method(self):
        # Pick up at physical store
        pick_store_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx",
            params={
                "_a": "selectFulfillmentLocationAction",
                "_m": "checkout.fulfillment.fulfillmentOptions",
            },
            data={
                "checkout.fulfillment.fulfillmentOptions.selectFulfillmentLocation": "RETAIL",
            },
        )

    def fill_address(
        self,
        store_number: str,
        country: str,
        state: str,
        city: str,
        district: str,
    ):
        logger.info("Starting fill address...")

        data = {
            "checkout.fulfillment.pickupTab.pickup.storeLocator.showAllStores": "false",
            "checkout.fulfillment.pickupTab.pickup.storeLocator.selectStore": store_number,
            "checkout.fulfillment.pickupTab.pickup.storeLocator.searchInput": f"{state} {city} {district}",
            "checkout.fulfillment.pickupTab.pickup.storeLocator.address.stateCitySelectorForCheckout.city": city,
            "checkout.fulfillment.pickupTab.pickup.storeLocator.address.stateCitySelectorForCheckout.state": state,
            "checkout.fulfillment.pickupTab.pickup.storeLocator.address.stateCitySelectorForCheckout.provinceCityDistrict": f"{state} {city} {district}",
            "checkout.fulfillment.pickupTab.pickup.storeLocator.address.stateCitySelectorForCheckout.countryCode": country,
            "checkout.fulfillment.pickupTab.pickup.storeLocator.address.stateCitySelectorForCheckout.district": district,
        }
        store_resp = self.checkout_request(
            self.secure_host + "/shop/checkoutx",
            params={
                "_a": "search",
                "_m": "checkout.fulfillment.pickupTab.pickup.storeLocator",
            },
            data=data,
        )

        return store_resp

    def get_select_window(self, address_data: dict):
        pickups = address_data["body"]["checkout"]["fulfillment"]["pickupTab"]["pickup"]
        if "timeSlot" not in pickups:
            logger.info("No available pickup time")
            return None
        pick_data = pickups["timeSlot"]["dateTimeSlots"]["d"]
        selected_window = {}
        for idx, window in enumerate(pick_data["timeSlotWindows"]):
            assert isinstance(window, dict)
            deep_windows = list(window.values())[0] if window else None
            if not deep_windows:
                continue
            for deep_window in deep_windows:
                if not deep_window["isRestricted"]:
                    selected_window = pick_data
                    selected_window["window"] = deep_window
                    pick_date = pick_data["pickUpDates"][idx]
                    selected_window["date"] = pick_date
                    logger.debug(f"Delivery raw: {selected_window}")
                    logger.info(
                        f"Delivery information: {pick_date.get('dayOfWeek')} {deep_window.get('Label')}"
                    )
                    break
            if selected_window:
                return selected_window
        logger.debug(f"Pick_data: {pick_data}")
        assert selected_window, "No pickup options found."

    def fill_contact(
        self,
        selected_window: dict,
        store_number: str,
        country: str,
        state: str,
        city: str,
        district: str,
    ):
        logger.info("Starting fill contact...")
        pickup_prefix = "checkout.fulfillment.pickupTab.pickup"
        dt_prefix = "checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots"
        data = {
            "checkout.fulfillment.fulfillmentOptions.selectFulfillmentLocation": "RETAIL",
            f"{pickup_prefix}.storeLocator.showAllStores": "false",
            f"{pickup_prefix}.storeLocator.selectStore": store_number,
            f"{pickup_prefix}.storeLocator.searchInput": f"{state} {city} {district}",
            f"{pickup_prefix}.storeLocator.address.stateCitySelectorForCheckout.city": city,
            f"{pickup_prefix}.storeLocator.address.stateCitySelectorForCheckout.state": state,
            f"{pickup_prefix}.storeLocator.address.stateCitySelectorForCheckout.provinceCityDistrict": f"{state} {city} {district}",
            f"{pickup_prefix}.storeLocator.address.stateCitySelectorForCheckout.countryCode": country,
            f"{pickup_prefix}.storeLocator.address.stateCitySelectorForCheckout.district": district,
            f"{dt_prefix}.startTime": selected_window["window"]["checkInStart"],
            f"{dt_prefix}.displayEndTime": selected_window["displayEndTime"],
            f"{dt_prefix}.isRecommended": str(selected_window["isRecommended"]).lower(),
            f"{dt_prefix}.endTime": selected_window["window"]["checkInEnd"],
            f"{dt_prefix}.date": selected_window["date"]["date"],
            f"{dt_prefix}.timeSlotId": selected_window["window"]["SlotId"],
            f"{dt_prefix}.signKey": selected_window["window"]["signKey"],
            f"{dt_prefix}.timeZone": selected_window["window"]["timeZone"],
            f"{dt_prefix}.timeSlotValue": selected_window["window"]["timeSlotValue"],
            f"{dt_prefix}.dayRadio": selected_window["dayRadio"],
            f"{dt_prefix}.isRestricted": selected_window["isRestricted"] or "",
            f"{dt_prefix}.displayStartTime": selected_window["displayStartTime"],
        }

        contact_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx",
            params={
                "_a": "continueFromFulfillmentToPickupContact",
                "_m": "checkout.fulfillment",
            },
            data=data,
        )

    def fill_recipient(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        idcard: str,
    ):
        logger.info("Starting fill recipient...")

        data = {
            "checkout.pickupContact.selfPickupContact.selfContact.address.lastName": last_name,
            "checkout.pickupContact.selfPickupContact.selfContact.address.firstName": first_name,
            "checkout.pickupContact.selfPickupContact.selfContact.address.emailAddress": email,
            "checkout.pickupContact.selfPickupContact.selfContact.address.fullDaytimePhone": phone,
            "checkout.pickupContact.selfPickupContact.nationalIdSelf.nationalIdSelf": idcard,
            "checkout.pickupContact.eFapiaoSelector.selectFapiao": "none",  # e_personal
        }
        review_bill_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx",
            params={
                "_a": "continueFromPickupContactToBilling",
                "_m": "checkout.pickupContact",
            },
            data=data,
        )

    def fill_pay_method(self, payment: str, number: int):
        logger.info("Starting fill pay methods...")
        data = {
            "checkout.billing.billingOptions.selectBillingOption": payment,
            "checkout.locationConsent.locationConsent": "false",
        }
        bill_option_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx/billing",
            params={
                "_a": "selectBillingOptionAction",
                "_m": "checkout.billing.billingOptions",
            },
            data=data,
        )
        data = {
            "checkout.billing.billingOptions.selectBillingOption": payment,
            "checkout.billing.billingOptions.selectedBillingOptions.installments.installmentOptions.selectInstallmentOption": str(
                number
            ),
        }
        bill_confirm_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx/billing",
            params={
                "_a": "continueFromBillingToReview",
                "_m": "checkout.billing",
            },
            data=data,
        )

    def finish_checkout(self, show_cookie: bool = False):
        logger.info("Starting final checkout...")

        place_order_data = self.get_place_order_data()

        self.get_page_with_meta(
            self.secure_host + place_order_data["head"]["data"]["url"], None
        )

        status_data = self.get_checkout_status_x()

        if show_cookie:
            cookie_str = "; ".join(
                [f"{k}={v}" for k, v in self.session.session.cookies.get_dict().items()]
            )

            logger.info("Order page cookies: %s", cookie_str)

        while True:
            thank_data = self.get_page_with_meta(
                self.secure_host + place_order_data["head"]["data"]["url"], None
            )
            thank_you_interstitial = thank_data.get("thankYouInterstitial") or {}
            order_data = thank_you_interstitial.get("d") or {}
            order_number = order_data.get("orderNumber")
            if order_number:
                logger.info(f"Order done, order number: {order_number}.")
                break
            time.sleep(1)

    def get_place_order_data(self):
        logger.info("Get order data...")
        place_order_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx",
            params={
                "_a": "continueFromReviewToProcess",
                "_m": "checkout.review.placeOrder",
            },
            assert_code=302,
        )
        if place_order_data is False:
            time.sleep(1)
            return self.get_place_order_data()
        return place_order_data

    def get_checkout_status_x(self):
        logger.info("Get order status...")
        status_data = self.checkout_request(
            self.secure_host + "/shop/checkoutx/statusX",
            params={
                "_a": "checkStatus",
                "_m": "spinner",
            },
            assert_code=302,
        )
        if status_data is False:
            time.sleep(1)
            return self.get_checkout_status_x()
        return status_data

    def get_page_with_meta(self, url, params, data: Optional[dict] = None):
        page_resp = self.session.get(url, params=params, data=data)
        assert page_resp.status_code == 200
        page_content = page_resp.text
        assert "x-aos-stk" in page_content
        cart_meta_match = re.search(
            r"<script id=\"init_data\" type=\"application/json\">(.+?)</script>",
            page_content,
            flags=re.DOTALL,
        )
        assert cart_meta_match
        meta_json = cart_meta_match.group(1)
        meta_json_data = json.loads(meta_json.strip())
        headers = meta_json_data["meta"]["h"]
        self.session.session.headers.update(headers)

        return meta_json_data


@dataclasses.dataclass()
class PoolData(object):
    order: Order
    timestamp: float
    available: bool = True


class OrderSessionPool(object):
    def __init__(self, timeout: int = 60 * 30) -> None:
        super().__init__()
        self.timeout = timeout
        self.pools: list[PoolData] = []
        self.redundant_time = 60 * 5
        self.lock = threading.Lock()
        self.is_stop = False

    def start(self, order_data: OrderSchema):
        thread = threading.Thread(
            target=self.handle_pool, args=(order_data,), name="OrderPool"
        )
        thread.start()

    def handle_pool(self, order_data: OrderSchema, max_count: int = 3):
        timeout = self.timeout - self.redundant_time
        logger.info("Start maintaining the order session pool...")
        while not self.is_stop:
            for pool in self.pools:
                if time.time() - pool.timestamp >= timeout:
                    pool.available = False
            with self.lock:
                self.pools = [i for i in self.pools if i.available]

            logger.info(f"Number of available order session pools: {len(self.pools)}")

            while max_count - len(self.pools) > 0:
                pool_data = self.new(order_data)
                with self.lock:
                    self.pools.append(pool_data)
            time.sleep(30)

    def new(self, order_data: OrderSchema) -> PoolData:
        try:
            create_timestamp = time.time()
            order = Order(order_data.country)
            order.init_order(order_data)
            return PoolData(order=order, timestamp=create_timestamp)
        except Exception as e:
            logging.exception("Init order fail with error", exc_info=e)
            time.sleep(1)
            return self.new(order_data)

    def stop(self):
        self.is_stop = True

    def get(self) -> Order:
        while True:
            if not self.pools:
                time.sleep(0.1)
                continue
            with self.lock:
                pool_data = self.pools.pop(0)
            return pool_data.order
