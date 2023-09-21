import abc
import logging
import time
from typing import Optional
from urllib.parse import quote_plus

import requests


class NotificationBase(object):
    name: str

    def __init__(self, token: Optional[str] = None) -> None:
        super().__init__()
        self.token = token
        self.last_push_maps: dict[str, float] = {}

    def push(
        self, title: str, content: str, key: str = "default", min_interval: int = 0
    ):
        if (
            min_interval
            and self.last_push_maps.get(key)
            and (time.time() - self.last_push_maps[key]) < min_interval
        ):
            logging.info("Pushing too frequently, wait for the next push")
            return

        self.push_data(title, content)

        self.last_push_maps[key] = time.time()

    @abc.abstractmethod
    def push_data(self, title: str, content: str):
        pass


class DingTalkNotification(NotificationBase):
    name = "dingtalk"

    def push_data(self, title: str, content: str):
        assert self.token, "Access_token credentials must be provided"
        url = f"https://oapi.dingtalk.com/robot/send?access_token={self.token}"
        resp = requests.post(
            url,
            json={
                "msgtype": "text",
                "text": {"content": title + "\r\n\r\n" + content},
                "at": {"isAtAll": 0},
            },
        )
        resp_json = resp.json()

        assert resp_json.get("errcode") == 0, resp_json.get("errmsg")


class BarkNotification(NotificationBase):
    name = "bark"

    def __init__(
        self,
        token: Optional[str] = None,
        host: Optional[str] = None,
    ) -> None:
        super().__init__(token=token)
        self.host = (host or "https://api.day.app").rstrip("/")

    def push_data(self, title: str, content: str):
        assert self.token, "Token credentials must be provided"
        title, content = quote_plus(title), quote_plus(content)
        url = f"{self.host}/{self.token}/{title}/{content}"
        resp = requests.get(url)
        resp_json = resp.json()

        assert resp_json.get("code") == 200, resp_json.get("message")


class FeishuNotification(NotificationBase):
    name = "feishu"

    def push_data(self, title: str, content: str):
        assert self.token, "token credentials must be provided"
        url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.token}"
        resp = requests.post(
            url,
            json={
                "msg_type": "text",
                "content": {"text": title + "\r\n\r\n" + content},
            },
        )
        resp_json = resp.json()

        assert resp_json.get("code") == 0, resp_json.get("msg")
