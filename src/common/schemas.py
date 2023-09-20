import dataclasses


@dataclasses.dataclass()
class ShopSchema(object):
    country: str
    models: list[str]
    location: str = ''
    postal_code: str = ''
    state: str = ''


@dataclasses.dataclass()
class DeliverySchema(object):
    state: str
    city: str
    district: str
    store_name: str
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
    carrier_model: str = ''

    def key(self):
        return "-".join([self.type, self.capacity, self.color])

    def intro(self):
        return " ".join(
            [i for i in [
                self.model,
                self.type,
                self.capacity,
                self.carrier_model,
                self.color_display,
                self.price_display,
            ] if i]
        )
