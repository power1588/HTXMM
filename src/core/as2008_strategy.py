import logging
import numpy as np
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv

class AS2008Strategy:
    def __init__(self, config: Dict):
        """
        初始化AS2008做市策略
        
        Args:
            config: 策略配置参数
        """
        # 加载环境变量
        load_dotenv()
        
        self.logger = logging.getLogger('as2008_strategy')
        
        # 策略参数
        self.inventory_target = float(os.getenv('INVENTORY_TARGET', 0))
        self.inventory_limit = float(os.getenv('INVENTORY_LIMIT', 10))
        self.risk_aversion = float(os.getenv('RISK_AVERSION', 0.1))
        self.order_size = float(os.getenv('ORDER_SIZE', 0.1))
        self.spread_multiplier = float(os.getenv('SPREAD_MULTIPLIER', 1.0))
        
        # 风险控制参数
        self.max_position_limit = float(os.getenv('MAX_POSITION_LIMIT', 20))
        self.max_order_size = float(os.getenv('MAX_ORDER_SIZE', 1.0))
        self.max_spread_ratio = float(os.getenv('MAX_SPREAD_RATIO', 0.01))
        self.min_profit_ratio = float(os.getenv('MIN_PROFIT_RATIO', 0.0005))
        
        # 订单簿参数
        self.orderbook_depth = int(os.getenv('ORDERBOOK_DEPTH', 5))
        self.rebalance_threshold = float(os.getenv('REBALANCE_THRESHOLD', 0.1))
        
        # 状态变量
        self.current_inventory = 0
        self.mid_price = 0
        self.spread = 0
        
        # 初始化参数
        self.kappa = config.get('kappa', 0.1)  # 库存调整速度
        self.alpha = config.get('alpha', 0.1)  # 风险厌恶系数
        self.gamma = config.get('gamma', 0.1)  # 库存惩罚系数
        self.sigma = config.get('sigma', 0.1)  # 波动率
        self.delta = config.get('delta', 0.1)  # 订单簿深度参数
        
    def calculate_optimal_quotes(self, orderbook: Dict, current_position: float) -> List[Dict]:
        """
        计算最优报价
        
        Args:
            orderbook: 当前订单簿数据
            current_position: 当前持仓
            
        Returns:
            List[Dict]: 目标订单列表
        """
        try:
            # 更新当前持仓
            self.current_inventory = current_position
            
            # 计算中间价和价差
            best_bid = float(orderbook['bids'][0][0])
            best_ask = float(orderbook['asks'][0][0])
            self.mid_price = (best_bid + best_ask) / 2
            self.spread = best_ask - best_bid
            
            # 计算库存调整项
            inventory_adjustment = self.kappa * current_position
            
            # 计算风险调整项
            risk_adjustment = self.alpha * self.sigma**2 * current_position
            
            # 计算最优买卖价差
            spread = self.gamma * self.sigma**2 + 2 * self.delta
            
            # 计算最优报价
            bid_price = self.mid_price - spread/2 - inventory_adjustment - risk_adjustment
            ask_price = self.mid_price + spread/2 - inventory_adjustment - risk_adjustment
            
            # 确保报价在合理范围内
            bid_price = max(bid_price, best_bid * (1 - self.max_spread_ratio))
            ask_price = min(ask_price, best_ask * (1 + self.max_spread_ratio))
            
            # 确保价差满足最小要求
            if (ask_price - bid_price) / bid_price < self.min_profit_ratio:
                spread = self.min_profit_ratio * bid_price
                bid_price = self.mid_price - spread/2
                ask_price = self.mid_price + spread/2
            
            # 计算订单大小
            order_size = self.order_size
            
            # 构建订单
            orders = [
                {
                    'type': 'limit',
                    'side': 'buy',
                    'price': round(bid_price, self.max_spread_ratio),
                    'amount': round(order_size, self.max_order_size)
                },
                {
                    'type': 'limit',
                    'side': 'sell',
                    'price': round(ask_price, self.max_spread_ratio),
                    'amount': round(order_size, self.max_order_size)
                }
            ]
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal quotes: {str(e)}")
            return []
        
    def calculate_order_sizes(self, orderbook: Dict) -> Tuple[float, float]:
        """
        计算订单大小
        
        Args:
            orderbook: 当前订单簿数据
            
        Returns:
            Tuple[float, float]: (买单大小, 卖单大小)
        """
        # 计算库存偏差
        inventory_deviation = self.current_inventory - self.inventory_target
        
        # 根据库存偏差调整订单大小
        base_size = self.order_size
        bid_size = base_size * (1 - inventory_deviation / self.inventory_limit)
        ask_size = base_size * (1 + inventory_deviation / self.inventory_limit)
        
        # 确保订单大小在限制范围内
        bid_size = min(bid_size, self.max_order_size)
        ask_size = min(ask_size, self.max_order_size)
        
        return bid_size, ask_size
        
    def should_rebalance(self, current_position: float) -> bool:
        """
        检查是否需要再平衡
        
        Args:
            current_position: 当前持仓
            
        Returns:
            bool: 是否需要再平衡
        """
        try:
            position_deviation = abs(current_position - self.inventory_target)
            return position_deviation > self.rebalance_threshold * self.inventory_limit
            
        except Exception as e:
            self.logger.error(f"Error checking rebalance: {str(e)}")
            return False
        
    def calculate_rebalance_orders(self, current_position: float) -> List[Dict]:
        """
        计算再平衡订单
        
        Args:
            current_position: 当前持仓
            
        Returns:
            List[Dict]: 再平衡订单列表
        """
        try:
            target_position = self.inventory_target
            position_diff = target_position - current_position
            
            # 确定交易方向
            side = 'buy' if position_diff > 0 else 'sell'
            
            # 计算订单数量
            num_orders = int(abs(position_diff) / self.order_size)
            
            # 构建订单
            orders = []
            for _ in range(num_orders):
                orders.append({
                    'type': 'limit',
                    'side': side,
                    'price': None,  # 市价单
                    'amount': round(self.order_size, self.max_order_size)
                })
                
            return orders
            
        except Exception as e:
            self.logger.error(f"Error calculating rebalance orders: {str(e)}")
            return []
            
    def get_market_metrics(self) -> Dict:
        """
        获取市场指标
        
        Returns:
            Dict: 市场指标
        """
        try:
            return {
                'mid_price': self.mid_price,
                'spread': self.spread,
                'current_inventory': self.current_inventory,
                'inventory_target': self.inventory_target,
                'inventory_limit': self.inventory_limit,
                'kappa': self.kappa,
                'alpha': self.alpha,
                'gamma': self.gamma,
                'sigma': self.sigma,
                'delta': self.delta
            }
        except Exception as e:
            self.logger.error(f"Error getting market metrics: {str(e)}")
            return {} 