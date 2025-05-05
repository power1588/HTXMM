# -*- coding: utf-8 -*-

import asyncio
import logging
from typing import Dict, Optional
import ccxt.pro as ccxtpro
from ccxt import AuthenticationError, NetworkError, ExchangeError

from ..market.market_data import MarketData
from ..order.order_manager import OrderManager
from ..risk.risk_manager import RiskManager
from ..utils.logger import setup_logger
from .as2008_strategy import AS2008Strategy

class MarketMaker:
    def __init__(
        self,
        exchange_id: str,
        symbol: str,
        api_key: str,
        secret: str,
        config: Dict
    ):
        """
        初始化做市商策略
        
        Args:
            exchange_id: 交易所ID (例如: 'htx')
            symbol: 交易对 (例如: 'BTC/USDT:USDT')
            api_key: API密钥
            secret: API密钥
            config: 策略配置
        """
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.api_key = api_key
        self.secret = secret
        self.config = config
        
        # 初始化交易所连接
        exchange_options = {
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap'
            }
        }
        
        # 创建交易所实例
        self.exchange = ccxtpro.htx(exchange_options)
        
        # 设置API URLs
        self.exchange.urls['api'] = {
            'public': 'https://api.hbdm.vn/linear-swap-api/v1',
            'private': 'https://api.hbdm.vn/linear-swap-api/v1',
            'ws': 'wss://api.hbdm.vn/linear-swap-ws'
        }
        
        # 设置市场类型
        self.exchange.options['defaultType'] = 'swap'
        # self.exchange.options['defaultSubType'] = 'linear-swap'
        
        # 初始化各个组件
        self.market_data = MarketData(self.exchange, symbol)
        self.order_manager = OrderManager(self.exchange, symbol)
        self.risk_manager = RiskManager(config)
        self.strategy = AS2008Strategy(config)
        
        # 设置日志
        self.logger = setup_logger('market_maker')
        
        # 状态变量
        self.running = False
        self.positions = {}
        self.orders = {}
        
    async def start(self):
        """启动做市商策略"""
        self.running = True
        self.logger.info("Starting market maker strategy...")
        
        retry_count = 0
        max_retries = 3
        retry_delay = 5  # seconds
        
        while retry_count < max_retries:
            try:
                # 加载市场信息
                await self.exchange.load_markets()
                self.logger.info("Markets loaded successfully")
                
                # 验证连接
                await self.validate_connection()
                
                # 启动市场数据订阅
                await self.market_data.start()
                self.logger.info("Market data subscription started")
                
                # 获取市场信息
                market_info = self.market_data.get_market_info()
                self.logger.info(f"Market info: {market_info}")
                
                # 重置重试计数
                retry_count = 0
                
                # 启动主循环
                while self.running:
                    try:
                        # 获取最新市场数据
                        orderbook = await self.market_data.get_orderbook()
                        if not orderbook:
                            self.logger.warning("No orderbook data available, waiting...")
                            await asyncio.sleep(1)
                            continue
                        
                        # 获取当前持仓
                        positions = await self.order_manager.get_positions()
                        current_position = float(positions.get(self.symbol, {}).get('contracts', 0))
                        
                        # 打印市场BBO信息
                        best_bid = float(orderbook['bids'][0][0])
                        best_ask = float(orderbook['asks'][0][0])
                        self.logger.info(f"Market BBO - Bid: {best_bid:.2f}, Ask: {best_ask:.2f}, Spread: {(best_ask-best_bid)/best_bid*100:.4f}%")
                        
                        # 检查是否需要再平衡
                        if self.strategy.should_rebalance(current_position):
                            self.logger.info("Rebalancing position...")
                            target_orders = self.strategy.calculate_rebalance_orders(current_position)
                        else:
                            # 计算目标订单
                            target_orders = self.strategy.calculate_optimal_quotes(orderbook, current_position)
                            
                            # 打印做市报价信息
                            if target_orders:
                                bid_order = next((o for o in target_orders if o['side'] == 'buy'), None)
                                ask_order = next((o for o in target_orders if o['side'] == 'sell'), None)
                                if bid_order and ask_order:
                                    self.logger.info(f"Market Making Quotes - Bid: {bid_order['price']:.2f}, Ask: {ask_order['price']:.2f}, Spread: {(ask_order['price']-bid_order['price'])/bid_order['price']*100:.4f}%")
                        
                        # 风险管理检查
                        if not self.risk_manager.check_risk(target_orders):
                            self.logger.warning("Risk check failed, skipping order placement")
                            continue
                        
                        # 更新订单
                        await self.order_manager.update_orders(target_orders)
                        
                        # 记录市场指标
                        metrics = self.strategy.get_market_metrics()
                        self.logger.info(f"Market metrics: {metrics}")
                        
                        # 等待下一次迭代
                        await asyncio.sleep(self.config['order_update_interval'])
                        
                    except ccxt.NetworkError as e:
                        self.logger.error(f"Network error in main loop: {str(e)}")
                        await asyncio.sleep(retry_delay)
                    except ccxt.ExchangeError as e:
                        self.logger.error(f"Exchange error in main loop: {str(e)}")
                        await asyncio.sleep(retry_delay)
                    except Exception as e:
                        self.logger.error(f"Unexpected error in main loop: {str(e)}")
                        await asyncio.sleep(retry_delay)
                    
            except AuthenticationError as e:
                self.logger.error(f"Authentication failed: {str(e)}")
                break  # 认证错误直接退出
            except (NetworkError, ExchangeError) as e:
                retry_count += 1
                self.logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    self.logger.error("Max retries reached, stopping strategy")
                    break
            except Exception as e:
                self.logger.error(f"Fatal error: {str(e)}")
                break
        
        await self.stop()
    
    async def validate_connection(self):
        """验证交易所连接"""
        try:
            # 测试API连接
            await self.exchange.fetch_balance()
            self.logger.info("API connection validated successfully")
            return True
        except Exception as e:
            self.logger.error(f"API connection validation failed: {str(e)}")
            raise
    
    async def stop(self):
        """停止做市商策略"""
        self.running = False
        self.logger.info("Stopping market maker strategy...")
        
        # 取消所有订单
        await self.order_manager.cancel_all_orders()
        
        # 关闭市场数据订阅
        await self.market_data.stop()
        
        # 关闭交易所连接
        await self.exchange.close() 