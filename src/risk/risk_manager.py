import logging
from typing import Dict, List
import numpy as np

class RiskManager:
    def __init__(self, config: Dict):
        """
        初始化风险管理器
        
        Args:
            config: 风险配置参数
        """
        self.config = config
        self.logger = logging.getLogger('risk_manager')
        self.position_limit = config.get('position_limit', 100)  # 最大持仓限制
        self.max_order_size = config.get('max_order_size', 10)  # 最大单笔订单大小
        self.max_spread = config.get('max_spread', 0.01)  # 最大价差比例
        self.min_profit = config.get('min_profit', 0.0005)  # 最小利润比例
        
    def check_risk(self, orders: List[Dict]) -> bool:
        """
        检查订单风险
        
        Args:
            orders: 订单列表
            
        Returns:
            bool: 是否通过风险检查
        """
        try:
            # 检查订单数量
            if len(orders) > self.config['max_orders']:
                self.logger.warning(f"Too many orders: {len(orders)} > {self.config['max_orders']}")
                return False
                
            # 检查订单大小
            for order in orders:
                if order['amount'] > self.config['order_size']:
                    self.logger.warning(f"Order size too large: {order['amount']} > {self.config['order_size']}")
                    return False
                    
            # 检查价差
            bids = [o for o in orders if o['side'] == 'buy']
            asks = [o for o in orders if o['side'] == 'sell']
            
            if bids and asks:
                best_bid = max(b['price'] for b in bids)
                best_ask = min(a['price'] for a in asks)
                spread = (best_ask - best_bid) / best_bid
                
                if spread < self.config['min_spread']:
                    self.logger.warning(f"Spread too small: {spread} < {self.config['min_spread']}")
                    return False
                    
                if spread > self.config['max_spread']:
                    self.logger.warning(f"Spread too large: {spread} > {self.config['max_spread']}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error in risk check: {str(e)}")
            return False
        
    def _check_order_sizes(self, target_orders: Dict) -> bool:
        """检查订单大小是否在限制范围内"""
        for side in ['bids', 'asks']:
            for _, size in target_orders.get(side, []):
                if size > self.max_order_size:
                    return False
        return True
        
    def _check_spread(self, target_orders: Dict) -> bool:
        """检查价差是否在合理范围内"""
        bids = target_orders.get('bids', [])
        asks = target_orders.get('asks', [])
        
        if not bids or not asks:
            return False
            
        best_bid = max(bids, key=lambda x: x[0])[0]
        best_ask = min(asks, key=lambda x: x[0])[0]
        
        spread = (best_ask - best_bid) / best_bid
        return spread <= self.max_spread
        
    def _check_profit(self, target_orders: Dict) -> bool:
        """检查预期利润是否满足要求"""
        bids = target_orders.get('bids', [])
        asks = target_orders.get('asks', [])
        
        if not bids or not asks:
            return False
            
        # 计算平均买入价和卖出价
        avg_bid = np.mean([price for price, _ in bids])
        avg_ask = np.mean([price for price, _ in asks])
        
        # 计算预期利润
        expected_profit = (avg_ask - avg_bid) / avg_bid
        return expected_profit >= self.min_profit
        
    def check_position_risk(self, position: float) -> bool:
        """
        检查持仓风险
        
        Args:
            position: 当前持仓
            
        Returns:
            bool: 是否通过风险检查
        """
        try:
            if abs(position) > self.position_limit:
                self.logger.warning(f"Position too large: {position} > {self.position_limit}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in position risk check: {str(e)}")
            return False
            
    def check_inventory_risk(self, inventory: float) -> bool:
        """
        检查库存风险
        
        Args:
            inventory: 当前库存
            
        Returns:
            bool: 是否通过风险检查
        """
        try:
            target = self.config['inventory_target']
            range = self.config['inventory_range']
            
            if abs(inventory - target) > range:
                self.logger.warning(f"Inventory out of range: {inventory} not in [{target-range}, {target+range}]")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in inventory risk check: {str(e)}")
            return False 