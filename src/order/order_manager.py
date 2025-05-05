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
        self.orders = {}
        self.logger = logging.getLogger('order_manager')
        
    async def get_positions(self) -> Dict:
        """获取当前持仓"""
        try:
            positions = await self.exchange.fetch_positions([self.symbol])
            return {p['symbol']: p for p in positions}
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            return {}
            
    async def get_open_orders(self) -> List[Dict]:
        """获取当前未成交订单"""
        try:
            orders = await self.exchange.fetch_open_orders(self.symbol)
            return orders
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {str(e)}")
            return []
            
    async def place_order(self, order: Dict) -> Optional[Dict]:
        """下单"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                result = await self.exchange.create_order(
                    symbol=self.symbol,
                    type=order['type'],
                    side=order['side'],
                    amount=order['amount'],
                    price=order['price']
                )
                self.orders[result['id']] = result
                return result
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    self.logger.error(f"Failed to place order after {max_retries} retries: {str(e)}")
                    return None
                else:
                    self.logger.warning(f"Retry {retry_count}/{max_retries} placing order: {str(e)}")
                    await asyncio.sleep(1)
                    
    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await self.exchange.cancel_order(order_id, self.symbol)
                if order_id in self.orders:
                    del self.orders[order_id]
                return True
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    self.logger.error(f"Failed to cancel order after {max_retries} retries: {str(e)}")
                    return False
                else:
                    self.logger.warning(f"Retry {retry_count}/{max_retries} canceling order: {str(e)}")
                    await asyncio.sleep(1)
                    
    async def cancel_all_orders(self):
        """取消所有订单"""
        try:
            orders = await self.get_open_orders()
            for order in orders:
                await self.cancel_order(order['id'])
        except Exception as e:
            self.logger.error(f"Error canceling all orders: {str(e)}")
            
    async def update_orders(self, target_orders: List[Dict]):
        """更新订单簿"""
        try:
            # 获取当前未成交订单
            current_orders = await self.get_open_orders()
            current_order_ids = {order['id'] for order in current_orders}
            
            # 取消不需要的订单
            for order in current_orders:
                if not any(
                    t['side'] == order['side'] and
                    t['price'] == order['price'] and
                    t['amount'] == order['amount']
                    for t in target_orders
                ):
                    await self.cancel_order(order['id'])
                    
            # 下新订单
            for order in target_orders:
                if not any(
                    c['side'] == order['side'] and
                    c['price'] == order['price'] and
                    c['amount'] == order['amount']
                    for c in current_orders
                ):
                    await self.place_order(order)
                    
        except Exception as e:
            self.logger.error(f"Error updating orders: {str(e)}") 