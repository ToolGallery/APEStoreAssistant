import dataclasses
from typing import Optional


@dataclasses.dataclass()
class ShopSchema(object):
    country: str
    models: list[str]
    location: str = ""
    postal_code: str = ""
    state: str = ""
    code: str = ""
    store_filters: list[str] = dataclasses.field(default_factory=lambda: [])


@dataclasses.dataclass()
class DeliverySchema(object):
    state: str
    city: str
    district: str
    store_name: str
    store_number: str
    model_name: str
    pickup_quote: str
    model: str
    status: str
    pickup_type: str

    def intro(self) -> str:
        return " ".join(
            [
                self.store_name,
                self.model_name,
                self.pickup_type,
                self.pickup_quote,
            ]
        )


@dataclasses.dataclass()
class ProductSchema(object):
    model: str
    type: str
    color: str
    capacity: str
    color_display: str
    price: float
    price_display: str
    price_currency: str
    carrier_model: str = ""

    def key(self):
        return "-".join([self.type, self.capacity, self.color])

    def intro(self):
        buffers = [
            i
            for i in [
                self.model,
                self.type,
                self.capacity,
                self.carrier_model,
                self.color_display,
                self.price_display,
            ]
            if i
        ]
        return " ".join(buffers)


@dataclasses.dataclass()
class PaymentSchema(object):
    label: str
    key: str
    value: str
    numbers: list[int]

    def intro(self):
        return " ".join(
            [self.value, self.label]
            + (
                ["support numbers: ", ",".join(map(str, self.numbers))]
                if self.numbers
                else []
            )
        )


@dataclasses.dataclass()
class OrderDeliverySchema(object):
    first_name: str
    last_name: str
    email: str
    phone: str
    idcard: str
    payment: str
    payment_number: int = 0


@dataclasses.dataclass()
class OrderSchema(object):
    model: str
    model_code: str
    country: str
    state: str = ""
    city: str = ""
    district: str = ""
    store_number: str = ""
    delivery: Optional[OrderDeliverySchema] = None
    ac_type: str = ""
    ac_model: str = ""
