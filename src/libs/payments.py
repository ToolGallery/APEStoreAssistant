import json
import logging
import os.path

from common.schemas import PaymentSchema


def get_payments(country: str):
    # current only support cn yet
    payments = []
    payments_path = os.path.abspath("statics/payments")
    file_path = payments_path + f"/{country}.json"
    if not os.path.isfile(file_path):
        logging.error(f"Payment methods does not support {country} yet.")
        return []
    with open(file_path, "r") as f:
        f_content = f.read()
        payments_json = json.loads(f_content)
        for payment in payments_json:
            payments.append(
                PaymentSchema(
                    label=payment.get("label", payment.get("labelImageAlt", "")),
                    key=payment["moduleKey"],
                    value=payment["value"],
                    numbers=payment.get("numbers", [])
                )
            )

    return payments
