import asyncio
from typing import Dict, Optional
import ccxt.pro as ccxt
import logging
from datetime import datetime, timedelta

class MarketData:
    def __init__(self, exchange: ccxt.Exchange, symbol: str):
        """
        初始化市场数据管理器
        
        Args:
            exchange: CCXT交易所实例
            symbol: 交易对
        """
        self.exchange = exchange
        self.symbol = symbol
        self.orderbook = None
        self.ticker = None
        self.trades = []
        self.running = False
        self.logger = logging.getLogger('market_data')
        
        # 连接状态
        self.last_orderbook_update = None
        self.last_ticker_update = None
        self.last_trades_update = None
        self.max_data_age = timedelta(seconds=10)  # 数据最大年龄
        self.reconnect_delay = 1  # 重连延迟（秒）
        self.max_reconnect_delay = 30  # 最大重连延迟（秒）
        
    async def start(self):
        """启动市场数据订阅"""
        self.running = True
        
        # 启动数据订阅
        self.orderbook_task = asyncio.create_task(self.watch_orderbook())
        self.ticker_task = asyncio.create_task(self.watch_ticker())
        self.trades_task = asyncio.create_task(self.watch_trades())
        
        # 启动连接监控
        self.monitor_task = asyncio.create_task(self.monitor_connection())
        
    async def stop(self):
        """停止市场数据订阅"""
        self.running = False
        
        # 取消所有任务
        tasks = [self.orderbook_task, self.ticker_task, self.trades_task, self.monitor_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
    async def monitor_connection(self):
        """监控数据连接状态"""
        while self.running:
            try:
                now = datetime.now()
                
                # 检查订单簿数据
                if (self.last_orderbook_update and 
                    now - self.last_orderbook_update > self.max_data_age):
                    self.logger.warning("Orderbook data is stale, restarting subscription")
                    if self.orderbook_task and not self.orderbook_task.done():
                        self.orderbook_task.cancel()
                    self.orderbook_task = asyncio.create_task(self.watch_orderbook())
                
                # 检查ticker数据
                if (self.last_ticker_update and 
                    now - self.last_ticker_update > self.max_data_age):
                    self.logger.warning("Ticker data is stale, restarting subscription")
                    if self.ticker_task and not self.ticker_task.done():
                        self.ticker_task.cancel()
                    self.ticker_task = asyncio.create_task(self.watch_ticker())
                
                # 检查交易数据
                if (self.last_trades_update and 
                    now - self.last_trades_update > self.max_data_age):
                    self.logger.warning("Trades data is stale, restarting subscription")
                    if self.trades_task and not self.trades_task.done():
                        self.trades_task.cancel()
                    self.trades_task = asyncio.create_task(self.watch_trades())
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in connection monitor: {str(e)}")
                await asyncio.sleep(5)
        
    async def watch_orderbook(self):
        """订阅订单簿数据"""
        retry_delay = self.reconnect_delay
        
        while self.running:
            try:
                orderbook = await self.exchange.watch_order_book(self.symbol)
                self.orderbook = orderbook
                self.last_orderbook_update = datetime.now()
                retry_delay = self.reconnect_delay  # 重置重连延迟
                
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error in orderbook subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error in orderbook subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except Exception as e:
                self.logger.error(f"Unexpected error in orderbook subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
    async def watch_ticker(self):
        """订阅ticker数据"""
        retry_delay = self.reconnect_delay
        
        while self.running:
            try:
                ticker = await self.exchange.watch_ticker(self.symbol)
                self.ticker = ticker
                self.last_ticker_update = datetime.now()
                retry_delay = self.reconnect_delay  # 重置重连延迟
                
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error in ticker subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error in ticker subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except Exception as e:
                self.logger.error(f"Unexpected error in ticker subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
    async def watch_trades(self):
        """订阅交易数据"""
        retry_delay = self.reconnect_delay
        
        while self.running:
            try:
                trades = await self.exchange.watch_trades(self.symbol)
                self.trades = trades[-100:]  # 保留最近100笔交易
                self.last_trades_update = datetime.now()
                retry_delay = self.reconnect_delay  # 重置重连延迟
                
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error in trades subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error in trades subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
            except Exception as e:
                self.logger.error(f"Unexpected error in trades subscription: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_reconnect_delay)
                
    async def get_orderbook(self) -> Optional[Dict]:
        """获取最新订单簿数据"""
        if (self.last_orderbook_update and 
            datetime.now() - self.last_orderbook_update > self.max_data_age):
            return None
        return self.orderbook
    
    async def get_ticker(self) -> Optional[Dict]:
        """获取最新ticker数据"""
        if (self.last_ticker_update and 
            datetime.now() - self.last_ticker_update > self.max_data_age):
            return None
        return self.ticker
    
    async def get_trades(self) -> list:
        """获取最新交易数据"""
        if (self.last_trades_update and 
            datetime.now() - self.last_trades_update > self.max_data_age):
            return []
        return self.trades 