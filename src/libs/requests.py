from typing import Optional

import requests


class Request(object):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:108.0) Gecko/20100101 Firefox/116.0",
    }

    def __init__(
        self, host: str, headers: Optional[dict] = None, timeout: int = 5
    ) -> None:
        super().__init__()
        self.session = requests.Session()
        self.request_host = host

        self.session.headers.update(self.default_headers)
        headers and self.session.headers.update(headers)

        self.default_timeout = timeout

    def request(self, method: str, *args, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if "timeout" in kwargs:
            kwargs["timeout"] = self.default_timeout
        return self.session.request(method, *args, **kwargs)

    def get(
        self,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ):
        return self.request(
            "GET", self.get_url(path), params=params, data=data, headers=headers
        )

    def get_url(self, path: str):
        if path.startswith("http"):
            return path
        return self.request_host + path

    def post(
        self,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        fetch_header: bool = True,
    ):
        headers = headers if headers else self.session.headers
        if fetch_header:
            headers = dict(headers) | {"X-Requested-With": "Fetch"}
        return self.request(
            "POST", self.get_url(path), params=params, data=data, headers=headers
        )
