# -*- coding: utf-8 -*-

import asyncio
import logging
from typing import Dict, List, Optional
import ccxt.pro as ccxt

class OrderManager:
    def __init__(self, exchange: ccxt.Exchange, symbol: str):
        """
        初始化订单管理器
        
        Args:
            exchange: CCXT交易所实例
            symbol: 交易对
        """
        self.exchange = exchange
        self.symbol = symbol
        self.logger = logging.getLogger('order_manager')
        
        # 设置市场类型
        self.exchange.options['defaultType'] = 'swap'
        self.exchange.options['defaultSubType'] = 'linear'
        self.exchange.options['broker'] = 'CCXT'
        
        # 设置WebSocket配置
        self.exchange.options['ws'] = {
            'url': 'wss://api.hbdm.vn/linear-swap-ws',
            'options': {
                'defaultType': 'swap',
                'defaultSubType': 'linear',
                'watchOrderBook': {
                    'method': 'watchOrderBookForLinearSwap',
                    'limit': 20,
                    'snapshotDelay': 5
                }
            }
        }
        
        # 设置API URL
        self.exchange.urls['api'] = {
            'public': 'https://api.hbdm.vn/linear-swap-api/v1',
            'private': 'https://api.hbdm.vn/linear-swap-api/v1',
            'ws': 'wss://api.hbdm.vn/linear-swap-ws'
        }
        
    async def get_positions(self) -> Dict:
        """获取当前持仓"""
        try:
            positions = await self.exchange.fetch_positions([self.symbol])
            return {pos['symbol']: pos for pos in positions if pos['symbol'] == self.symbol}
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            return {}
            
    async def get_open_orders(self) -> List:
        """获取未成交订单"""
        try:
            return await self.exchange.fetch_open_orders(self.symbol)
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {str(e)}")
            return []
            
    async def create_order(self, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        创建订单
        
        Args:
            order_type: 订单类型 ('limit' 或 'market')
            side: 交易方向 ('buy' 或 'sell')
            amount: 交易数量
            price: 价格 (限价单必需)
            
        Returns:
            订单信息
        """
        try:
            params = {
                'type': 'swap',
                'subType': 'linear'
            }
            
            if order_type == 'limit':
                if not price:
                    raise ValueError("Price is required for limit orders")
                return await self.exchange.create_order(
                    self.symbol,
                    order_type,
                    side,
                    amount,
                    price,
                    params
                )
            else:
                return await self.exchange.create_order(
                    self.symbol,
                    order_type,
                    side,
                    amount,
                    None,
                    params
                )
        except Exception as e:
            self.logger.error(f"Error creating order: {str(e)}")
            return None
            
    async def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功取消
        """
        try:
            await self.exchange.cancel_order(order_id, self.symbol)
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            return False
            
    async def cancel_all_orders(self) -> bool:
        """
        取消所有订单
        
        Returns:
            是否成功取消所有订单
        """
        try:
            params = {
                'type': 'swap',
                'subType': 'linear'
            }
            await self.exchange.cancel_all_orders(self.symbol, params=params)
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {str(e)}")
            return False
            
    async def update_orders(self, target_orders: List[Dict]) -> bool:
        """
        更新订单
        
        Args:
            target_orders: 目标订单列表
            
        Returns:
            是否成功更新所有订单
        """
        try:
            # 获取当前未成交订单
            current_orders = await self.get_open_orders()
            
            # 取消所有当前订单
            if current_orders:
                await self.cancel_all_orders()
            
            # 创建新订单
            for order in target_orders:
                await self.create_order(
                    order['type'],
                    order['side'],
                    order['amount'],
                    order.get('price')
                )
                
            return True
        except Exception as e:
            self.logger.error(f"Error updating orders: {str(e)}")
            return False 