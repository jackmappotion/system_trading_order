import json
import requests
import pandas as pd

from ._controller import Controller


class StatusController:
    def __init__(self, controller):
        self.controller = controller

    def _fetch_balance(self):
        #
        path = "uapi/domestic-stock/v1/trading/inquire-balance"
        url = f"{self.controller.base_url}/{path}"
        #
        headers = self.controller.base_headers.copy()
        headers["tr_id"] = "TTTC8434R"
        #
        params = {
            "CANO": self.controller.acc_no_prefix,
            "ACNT_PRDT_CD": self.controller.acc_no_postfix,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        resp = requests.get(url, headers=headers, params=params)
        resp_data = resp.json()
        return resp_data

    def _fetch_orders(self):
        #
        path = "uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
        url = f"{self.controller.base_url}/{path}"
        #
        headers = self.controller.base_headers.copy()
        headers["tr_id"] = "TTTC8036R"
        #
        params = {
            "CANO": self.controller.acc_no_prefix,
            "ACNT_PRDT_CD": self.controller.acc_no_postfix,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0",
        }
        resp = requests.get(url, headers=headers, params=params)
        resp_data = resp.json()
        return resp_data

    def load_balance(self):
        balance_resp_data = self._fetch_balance()
        balance_df = pd.DataFrame(balance_resp_data["output2"])
        if len(balance_df) != 0:
            balance_df = self._format_balance(balance_df)
        return balance_df

    @staticmethod
    def _format_balance(balance_df):
        rename_column_dict = {"nass_amt": "total", "scts_evlu_amt": "stock"}
        balance_df.rename(columns=rename_column_dict, inplace=True)
        balance_df["cash"] = balance_df["total"].astype(float) - balance_df["stock"].astype(float)
        balance_df = balance_df.loc[:, ["cash", "stock", "total"]]
        return balance_df

    def load_position(self):
        balance_resp_data = self._fetch_balance()
        position_df = pd.DataFrame(balance_resp_data["output1"])
        if len(position_df) != 0:
            position_df = self._format_position(position_df)
        return position_df

    @staticmethod
    def _format_position(position_df):
        rename_column_dict = {
            "pdno": "stock_code",
            "prdt_name": "stock_nm",
            "pchs_avg_pric": "buying_price",
            "prpr": "current_price",
            "hldg_qty": "quantity",
        }
        position_df.rename(columns=rename_column_dict, inplace=True)

        calc_profit = lambda cp, bp: 100 * (cp - bp) / bp
        cp = position_df["current_price"].astype(float)
        bp = position_df["buying_price"].astype(float)
        position_df["profit_pct"] = calc_profit(cp, bp).apply(lambda x: str(round(x, 3)) + "%")

        position_df = position_df.loc[:, list(rename_column_dict.values()) + ["profit_pct"]]
        return position_df

    def load_order(self):
        order_resp_data = self._fetch_orders()
        order_df = pd.DataFrame(order_resp_data["output"])
        return order_df


class OrderController:
    def __init__(self, controller) -> None:
        self.controller = controller

    def _fetch_hashkey(self, data):
        path = "uapi/hashkey"
        url = f"{self.controller.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "appKey": self.controller.api_key,
            "appSecret": self.controller.api_secret,
            "User-Agent": "Mozilla/5.0",
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        haskkey = resp.json()["HASH"]
        return haskkey

    def make_market_buy_order(self, stock_code, quantity):
        path = "uapi/domestic-stock/v1/trading/order-cash"
        url = f"{self.controller.base_url}/{path}"

        data = {
            "CANO": self.controller.acc_no_prefix,
            "ACNT_PRDT_CD": self.controller.acc_no_postfix,
            "PDNO": stock_code,
            "ORD_DVSN": "01",  # 시장가 거래
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0",  # 시장가 거래
        }
        hashkey = self._fetch_hashkey(data)

        headers = {
            "content-type": "application/json",
            "authorization": self.controller.access_token,
            "appKey": self.controller.api_key,
            "appSecret": self.controller.api_secret,
            "tr_id": "TTTC0802U",  # buy
            "custtype": "P",
            "hashkey": hashkey,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_data = resp.json()
        resp_data["meta"] = {"stock_code": stock_code, "quantity": quantity}
        return resp_data

    def make_market_sell_order(self, stock_code, quantity):
        path = "uapi/domestic-stock/v1/trading/order-cash"
        url = f"{self.controller.base_url}/{path}"

        data = {
            "CANO": self.controller.acc_no_prefix,
            "ACNT_PRDT_CD": self.controller.acc_no_postfix,
            "PDNO": stock_code,
            "ORD_DVSN": "01",  # 시장가 거래
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0",  # 시장가 거래
        }
        hashkey = self._fetch_hashkey(data)

        headers = {
            "content-type": "application/json",
            "authorization": self.controller.access_token,
            "appKey": self.controller.api_key,
            "appSecret": self.controller.api_secret,
            "tr_id": "TTTC0801U",  # sell
            "custtype": "P",
            "hashkey": hashkey,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_data = resp.json()
        resp_data["meta"] = {"stock_code": stock_code, "quantity": quantity}
        return resp_data
