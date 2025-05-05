# 策略配置
STRATEGY_CONFIG = {
    # 交易所配置
    'exchange': {
        'id': 'htx',
        'symbol': 'BTC/USDT:USDT',
        'api_key': '',  # 需要填入实际的API密钥
        'secret': '',   # 需要填入实际的API密钥
    },
    
    # 订单配置
    'order': {
        'update_interval': 1.0,  # 订单更新间隔（秒）
        'max_retries': 3,        # 最大重试次数
        'retry_delay': 1.0,      # 重试延迟（秒）
    },
    
    # 风险控制配置
    'risk': {
        'position_limit': 100,   # 最大持仓限制
        'max_order_size': 10,    # 最大单笔订单大小
        'max_spread': 0.01,      # 最大价差比例
        'min_profit': 0.0005,    # 最小利润比例
    },
    
    # 做市策略配置
    'market_making': {
        'num_levels': 5,         # 订单簿深度
        'spread_ratio': 0.001,   # 基础价差比例
        'size_ratio': 0.1,       # 订单大小比例
        'rebalance_threshold': 0.1,  # 再平衡阈值
    },
} 