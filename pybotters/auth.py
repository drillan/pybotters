import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import aiohttp
from aiohttp.formdata import FormData
from aiohttp.hdrs import METH_GET
from multidict import CIMultiDict, MultiDict
from yarl import URL


class Auth:
    @staticmethod
    def bybit(args: Tuple[str, URL], kwargs: Dict[str, Any]) -> Tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data: Dict[str, Any] = kwargs['data'] or {}

        session: aiohttp.ClientSession = kwargs['session']
        key: str = session.__dict__['_apis'][Hosts.items[url.host].name][0]
        secret: bytes = session.__dict__['_apis'][Hosts.items[url.host].name][1]

        expires = str(int((time.time() - 1.0) * 1000))
        if method == METH_GET:
            query = MultiDict(url.query)
            if url.scheme == 'https':
                query.extend({'api_key': key, 'timestamp': expires})
                query_string = '&'.join(f'{k}={v}' for k, v in sorted(query.items()))
                sign = hmac.new(secret, query_string.encode(), hashlib.sha256).hexdigest()
                query.extend({'sign': sign})
            else:
                expires = str(int((time.time() + 1.0) * 1000))
                path = f'{method}/realtime{expires}'
                signature = hmac.new(secret, path.encode(), hashlib.sha256).hexdigest()
                query.extend({'api_key': key, 'expires': expires, 'signature': signature})
            url = url.with_query(query)
            args = (method, url, )
        else:
            data.update({'api_key': key, 'timestamp': expires})
            body = FormData(sorted(data.items()))()
            sign = hmac.new(secret, body._value, hashlib.sha256).hexdigest()
            body._value += f'&sign={sign}'.encode()
            body._size = len(body._value)
            kwargs.update({'data': body})

        return args

    @staticmethod
    def btcmex(args: Tuple[str, URL], kwargs: Dict[str, Any]) -> Tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data: Dict[str, Any] = kwargs['data'] or {}
        headers: CIMultiDict = kwargs['headers']

        session: aiohttp.ClientSession = kwargs['session']
        key: str = session.__dict__['_apis'][Hosts.items[url.host].name][0]
        secret: bytes = session.__dict__['_apis'][Hosts.items[url.host].name][1]

        path = url.raw_path_qs if url.scheme == 'https' else '/api/v1/signature'
        body = FormData(data)()
        expires = str(int(time.time() + 5.0))
        message = f'{method}{path}{expires}'.encode() + body._value
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        kwargs.update({'data': body})
        headers.update({'api-expires': expires, 'api-key': key, 'api-signature': signature})

        return args

    @staticmethod
    def binance(args: Tuple[str, URL], kwargs: Dict[str, Any]) -> Tuple[str, URL]:
        method: str = args[0]
        url: URL = args[1]
        data: Dict[str, Any] = kwargs['data'] or {}
        headers: CIMultiDict = kwargs['headers']

        session: aiohttp.ClientSession = kwargs['session']
        key: str = session.__dict__['_apis'][Hosts.items[url.host].name][0]
        secret: bytes = session.__dict__['_apis'][Hosts.items[url.host].name][1]

        expires = str(int(time.time() * 1000))
        if method == METH_GET:
            if url.scheme == 'https':
                query = MultiDict(url.query)
                query.extend({'timestamp': expires})
                query_string = '&'.join(f'{k}={v}' for k, v in query.items())
                signature = hmac.new(secret, query_string.encode(), hashlib.sha256).hexdigest()
                query.extend({'signature': signature})
                url = url.with_query(query)
                args = (method, url, )
        else:
            data.update({'timestamp': expires})
            body = FormData(data)()
            signature = hmac.new(secret, body._value, hashlib.sha256).hexdigest()
            body._value += f'&signature={signature}'.encode()
            body._size = len(body._value)
            kwargs.update({'data': body})
        headers.update({'X-MBX-APIKEY': key})

        return args


@dataclass
class Item:
    name: str
    # func: Callable[[Tuple[str, URL], Dict[str, Any]], Tuple[str, URL]]
    func: Any


class Hosts:
    items = {
        'www.btcmex.com': Item('btcmex', Auth.btcmex),
        'api.bybit.com': Item('bybit', Auth.bybit),
        'api.bytick.com': Item('bybit', Auth.bybit),
        'stream.bybit.com': Item('bybit', Auth.bybit),
        'stream.bytick.com': Item('bybit', Auth.bybit),
        'api-testnet.bybit.com': Item('bybit_testnet', Auth.bybit),
        'stream-testnet.bybit.com': Item('bybit_testnet', Auth.bybit),
        'api.binance.com': Item('binance', Auth.binance),
        'api1.binance.com': Item('binance', Auth.binance),
        'api2.binance.com': Item('binance', Auth.binance),
        'api3.binance.com': Item('binance', Auth.binance),
        'stream.binance.com': Item('binance', Auth.binance),
        'fapi.binance.com': Item('binance', Auth.binance),
        'fstream.binance.com': Item('binance', Auth.binance),
        'dapi.binance.com': Item('binance', Auth.binance),
        'dstream.binance.com': Item('binance', Auth.binance),
        'vapi.binance.com': Item('binance', Auth.binance),
        'vstream.binance.com': Item('binance', Auth.binance),
        'testnet.binancefuture.com': Item('binance_testnet', Auth.binance),
        'stream.binancefuture.com': Item('binance_testnet', Auth.binance),
        'testnet.binancefuture.com': Item('binance_testnet', Auth.binance),
        'dstream.binancefuture.com': Item('binance_testnet', Auth.binance),
        'testnet.binanceops.com': Item('binance_testnet', Auth.binance),
        'testnetws.binanceops.com': Item('binance_testnet', Auth.binance),
    }