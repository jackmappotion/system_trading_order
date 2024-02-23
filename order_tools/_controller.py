import json
import datetime
import requests


class Controller:
    def __init__(self, api_key: str, api_secret: str, acc_no: str):
        self.api_key = api_key
        self.api_secret = api_secret

        # account number
        self.acc_no = acc_no
        self.acc_no_prefix = acc_no.split("-")[0]
        self.acc_no_postfix = acc_no.split("-")[1]

        # etc
        self.base_url = "https://openapi.koreainvestment.com:9443"

    def set_access_token(self):
        if self._check_access_token():
            self._set_access_token()
        else:
            self._load_access_token()
            self._set_access_token()
        self._set_base_headers()

    def _check_access_token(self):
        try:
            with open("./token.json", "r") as f:
                data = json.load(f)

            expire_epoch = data["timestamp"]
            now_epoch = int(datetime.datetime.now().timestamp())

            if (
                (now_epoch - expire_epoch > 0)
                or (data["api_key"] != self.api_key)
                or (data["api_secret"] != self.api_secret)
            ):
                status = False
            else:
                status = True
            return status
        except IOError:
            return False

    def _load_access_token(self):
        path = "oauth2/tokenP"
        url = f"{self.base_url}/{path}"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_data = resp.json()
        # add extra information for the token verification
        now = datetime.datetime.now()
        resp_data["timestamp"] = int(now.timestamp()) + resp_data["expires_in"]
        resp_data["api_key"] = self.api_key
        resp_data["api_secret"] = self.api_secret

        # dump access token
        with open("./token.json", "w") as f:
            json.dump(resp_data, f, indent=4, ensure_ascii=False)

    def _set_access_token(self):
        with open("./token.json", "r") as f:
            data = json.load(f)
            self.access_token = f'Bearer {data["access_token"]}'

    def _set_base_headers(self):
        self.base_headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
        }
