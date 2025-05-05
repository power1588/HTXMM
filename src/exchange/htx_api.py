# -*- coding: utf-8 -*-

import asyncio
import logging
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Optional, Union
import aiohttp
from urllib.parse import urlencode
import urllib.parse


class HTXLinearSwapAPI:
    """HTX USDT永续合约API类"""
    
    def __init__(
        self,
        api_key: str = '',
        secret_key: str = '',
        base_url: str = 'https://api.hbdm.vn',
        ws_url: str = 'wss://api.hbdm.vn/linear-swap-ws',
        timeout: int = 10
    ):
        """
        初始化HTX USDT永续合约API
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            base_url: REST API基础URL
            ws_url: WebSocket API基础URL
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.ws_url = ws_url
        self.timeout = timeout
        self.logger = logging.getLogger('htx_api')
        self.session = None
        
    async def __aenter__(self):
        await self.init()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def init(self):
        """初始化aiohttp会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    def _sign(self, method: str, path: str, params: Dict) -> str:
        """
        生成签名
        
        Args:
            method: HTTP方法
            path: 请求路径
            params: 请求参数
            
        Returns:
            签名
        """
        # 1. 按照ASCII码的顺序对参数名进行排序
        sorted_params = sorted(params.items(), key=lambda d: d[0])
        
        # 2. 将参数名和参数值进行URL编码
        encoded_params = []
        for k, v in sorted_params:
            encoded_params.append(f"{urllib.parse.quote(str(k), safe='')}"
                                f"={urllib.parse.quote(str(v), safe='')}")
        
        # 3. 使用&将参数连接起来
        payload = '&'.join(encoded_params)
        
        # 4. 构造签名原文字符串
        host = urllib.parse.urlparse(self.base_url).netloc
        pre_signed_text = f"{method.upper()}\n{host}\n{path}\n{payload}"
        
        # 5. 使用HmacSHA256计算签名，并进行base64编码
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                pre_signed_text.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return signature
        
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        private: bool = False
    ) -> Dict:
        """
        发送HTTP请求
        
        Args:
            method: 请求方法 (GET/POST)
            path: API路径
            params: 请求参数
            private: 是否为私有接口
            
        Returns:
            响应数据
        """
        if self.session is None:
            await self.init()
            
        if params is None:
            params = {}
            
        # 构建请求参数
        request_params = params.copy()
            
        if private:
            # 添加认证参数
            timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
            request_params.update({
                'AccessKeyId': self.api_key,
                'SignatureMethod': 'HmacSHA256',
                'SignatureVersion': '2',
                'Timestamp': timestamp
            })
            
            # 生成签名
            signature = self._sign(method, path, request_params)
            request_params['Signature'] = signature
            
        # 构建完整URL
        url = f"{self.base_url}{path}"
        
        # 对于GET请求，将参数添加到URL中
        if method == 'GET':
            url = f"{url}?{urlencode(request_params)}"
            request_params = None
        elif private:
            # 对于私有接口的POST请求，将参数添加到URL中
            url = f"{url}?{urlencode(request_params)}"
            request_params = params  # 使用原始参数作为POST数据
            
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            if method == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    if response.content_type == 'text/plain':
                        text = await response.text()
                        return json.loads(text)
                    return await response.json()
            else:
                async with self.session.post(url, json=request_params, headers=headers) as response:
                    if response.content_type == 'text/plain':
                        text = await response.text()
                        return json.loads(text)
                    return await response.json()
        except Exception as e:
            self.logger.error(f"请求异常: {e}")
            return {'status': 'error', 'err_msg': str(e)}
            
    # 公共接口
    async def get_contract_info(self, contract_code: Optional[str] = None) -> Dict:
        """
        获取合约信息
        
        Args:
            contract_code: 合约代码，如'BTC-USDT'
            
        Returns:
            合约信息
        """
        path = '/linear-swap-api/v1/swap_contract_info'
        params = {}
        if contract_code:
            params['contract_code'] = contract_code.lower()
        return await self._request('GET', path, params)
        
    async def get_market_depth(
        self,
        contract_code: str,
        type: str = 'step0'
    ) -> Dict:
        """
        获取市场深度
        
        Args:
            contract_code: 合约代码，如'BTC-USDT'
            type: 深度类型，可选值：step0, step1, step2, step3, step4, step5
            
        Returns:
            市场深度数据
        """
        path = '/linear-swap-ex/market/depth'
        params = {
            'contract_code': contract_code.lower(),
            'type': type
        }
        return await self._request('GET', path, params)
        
    async def get_kline(
        self,
        contract_code: str,
        period: str = '1min',
        size: int = 150
    ) -> Dict:
        """
        获取K线数据
        
        Args:
            contract_code: 合约代码，如'ETH-USDT'
            period: K线周期，可选值：1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon
            size: 获取数量，范围[1,2000]
            
        Returns:
            K线数据
        """
        path = '/linear-swap-ex/market/history/kline'
        params = {
            'contract_code': contract_code,
            'period': period,
            'size': size
        }
        return await self._request('GET', path, params)
        
    # 私有接口
    async def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        path = '/linear-swap-api/v3/unified_account_info'
        return await self._request('POST', path, private=True)
        
    async def get_position_info(self, contract_code: Optional[str] = None) -> Dict:
        """
        获取持仓信息
        
        Args:
            contract_code: 合约代码，如'BTC-USDT'
            
        Returns:
            持仓信息
        """
        path = '/linear-swap-api/v1/swap_position_info'
        params = {}
        if contract_code:
            params['contract_code'] = contract_code.upper()
        return await self._request('POST', path, params, private=True)
        
    async def place_order(
        self,
        contract_code: str,
        direction: str,
        offset: str,
        price: float,
        volume: int,
        lever_rate: int = 20,
        order_price_type: str = 'limit'
    ) -> Dict:
        """
        下单
        
        Args:
            contract_code: 合约代码，如'BTC-USDT'
            direction: 买卖方向，'buy'或'sell'
            offset: 开平方向，'open'或'close'
            price: 价格
            volume: 数量
            lever_rate: 杠杆倍数
            order_price_type: 订单类型，默认为'limit'
            
        Returns:
            下单结果
        """
        path = '/linear-swap-api/v1/swap_order'
        params = {
            'contract_code': contract_code.upper(),
            'direction': direction,
            'offset': offset,
            'price': price,
            'volume': volume,
            'lever_rate': lever_rate,
            'order_price_type': order_price_type
        }
        return await self._request('POST', path, params, private=True)
        
    async def cancel_order(
        self,
        contract_code: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> Dict:
        """
        撤单
        
        Args:
            contract_code: 合约代码，如'ETH-USDT'
            order_id: 订单ID
            client_order_id: 客户订单ID
            
        Returns:
            撤单结果
        """
        path = '/linear-swap-api/v1/swap_cancel'
        params = {'contract_code': contract_code}
        if order_id:
            params['order_id'] = order_id
        if client_order_id:
            params['client_order_id'] = client_order_id
        return await self._request('POST', path, params, private=True)
        
    async def get_order_info(
        self,
        contract_code: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None
    ) -> Dict:
        """
        获取订单信息
        
        Args:
            contract_code: 合约代码，如'ETH-USDT'
            order_id: 订单ID
            client_order_id: 客户订单ID
            
        Returns:
            订单信息
        """
        path = '/linear-swap-api/v1/swap_order_info'
        params = {'contract_code': contract_code}
        if order_id:
            params['order_id'] = order_id
        if client_order_id:
            params['client_order_id'] = client_order_id
        return await self._request('POST', path, params, private=True)
        
    async def get_open_orders(
        self,
        contract_code: str,
        page_index: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        获取当前未成交订单
        
        Args:
            contract_code: 合约代码，如'ETH-USDT'
            page_index: 页码，从1开始
            page_size: 每页数量，范围[1,50]
            
        Returns:
            未成交订单列表
        """
        path = '/linear-swap-api/v1/swap_openorders'
        params = {
            'contract_code': contract_code,
            'page_index': page_index,
            'page_size': page_size
        }
        return await self._request('POST', path, params, private=True)
        
    async def get_order_history(
        self,
        contract_code: str,
        trade_type: int = 0,
        create_date: int = 90,
        page_index: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        获取历史订单
        
        Args:
            contract_code: 合约代码，如'ETH-USDT'
            trade_type: 交易类型，0:全部,1:买入开多,2:卖出开空,3:买入平空,4:卖出平多,5:卖出强平,6:买入强平,7:交割平多,8:交割平空
            create_date: 日期，默认90天
            page_index: 页码，从1开始
            page_size: 每页数量，范围[1,50]
            
        Returns:
            历史订单列表
        """
        path = '/linear-swap-api/v1/swap_hisorders'
        params = {
            'contract_code': contract_code,
            'trade_type': trade_type,
            'create_date': create_date,
            'page_index': page_index,
            'page_size': page_size
        }
        return await self._request('POST', path, params, private=True) 