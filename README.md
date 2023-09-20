# APEStoreAssistant
Reduce the waiting time

## Features
- [x] Query product list
- [x] Monitor inventory for multiple products
- [x] Support multiple countries
- [x] Notification support (Dingtalk | Bark)

## Use with Docker

### Supported options

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
```

### query products

```shell
docker run --rm toolgallery/ape-store-assistant:main -lp -c sg --code 15-pro
```

### Start monitoring

```shell
docker run --rm toolgallery/ape-store-assistant:main -c sg -p MTV13ZP/A MTV73ZP/A -l 329816
```


