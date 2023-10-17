# APEStoreAssistant

Reduce the waiting time

## Features

- [x] Query product list
- [x] Query address list
- [x] Monitor inventory for multiple products
- [x] Support multiple countries
- [x] Notification support (Dingtalk | Bark | Feishu)
- [x] Automatic order placement

## Usage

### Use with Docker

#### Supported options

```shell
docker run --rm toolgallery/ape-store-assistant:main -h
```

```
-p, --products PRODUCTS 
-l, --location LOCATION
-pc, --postal-code POSTAL_CODE
--state STATE
-lp, --list-products
-c COUNTRY, --country COUNTRY cn|hk-zh|sg|jp
--code CODE 15|15-pro
-i, --interval default:5 Query interval
--ac-type iphone14|iphone14promax|iphone14plus
    iphone14 for iPhone15/iPhone15 Pro, iphone14promax for iPhone15 Pro Max, iphone14plus for iPhone15 Plus
--ac-product AC+ Product
```

#### Query products

```shell
docker run --rm toolgallery/ape-store-assistant:main -lp -c sg --code 15-pro
```

#### Start monitoring

```shell
docker run --rm toolgallery/ape-store-assistant:main -c sg -p MTV13ZP/A MTV73ZP/A -l 329816

# message notification through dingtalk
docker run -e DINGTALK_TOKEN=yourtoken --rm toolgallery/ape-store-assistant:main -c sg -p MTV13ZP/A MTV73ZP/A -l 329816

# through bark, support both
docker run -e BARK_TOKEN=yourtoken --rm toolgallery/ape-store-assistant:main -c sg -p MTV13ZP/A MTV73ZP/A -l 329816
```

#### Query address
Only supports certain countries.

```shell
docker run --rm toolgallery/ape-store-assistant:main -la -c jp

# continue filter
docker run --rm toolgallery/ape-store-assistant:main -la -c jp -ft 青森県
docker run --rm toolgallery/ape-store-assistant:main -la -c jp -ft "青森県 山形県"
```

#### Query payment methods
Only supports certain countries.

```shell
docker run --rm toolgallery/ape-store-assistant:main -lpa -c cn
```

#### Automatic ordering
Only supports certain countries.

- Only supports a single model.
- Automatically select the nearest pickup time slot.
- After successfully placing an order, please check your email for the order information.

```shell
docker run --rm toolgallery/ape-store-assistant:main -c cn -p MPVG3CH/A -l "your location" -o -onc -1 --code 14

# -o Enable order support
# -onc The number of order notification reminders, effective after the order is successful, -1 means no limit.
# --code Product model code  // remove in the future.

# The following environment variables must be provided.
DELIVERY_FIRST_NAME 
DELIVERY_LAST_NAME
DELIVERY_EMAIL
DELIVERY_PHONE
DELIVERY_IDCARD # Last 4 digits of ID card
DELIVERY_PAYMENT #  Payment method, check through -lpa, such as installments0001321713
DELIVERY_PAYMENT_NUMBER # The number of installments, regular payment is 0.
```


### Supported environment variables

```shell
# dingtalk notification
DINGTALK_TOKEN
# bark notification
BARK_HOST
BARK_TOKEN
# feishu notification
FEISHU_TOKEN
```



