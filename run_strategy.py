import asyncio
import os
import logging
from dotenv import load_dotenv
from src.core.market_maker import MarketMaker
from src.utils.logger import setup_logger, get_log_file_path

# 配置日志
log_file = get_log_file_path()
logger = setup_logger('main', log_file)
logger.info(f"Log file: {log_file}")

async def main():
    try:
        # 加载环境变量
        load_dotenv('config.env')
        
        # 获取配置
        exchange_id = os.getenv('EXCHANGE_ID', 'htx')
        symbol = os.getenv('SYMBOL', 'ETH/USDT:USDT')
        api_key = os.getenv('API_KEY')
        secret = os.getenv('SECRET')
        
        if not api_key or not secret:
            raise ValueError("API key and secret must be provided in config.env file")
            
        # 构建配置字典
        config = {
            'order_update_interval': float(os.getenv('ORDER_UPDATE_INTERVAL', '1.0')),
            'max_position': float(os.getenv('MAX_POSITION', '0.1')),
            'min_spread': float(os.getenv('MIN_SPREAD', '0.0005')),
            'max_spread': float(os.getenv('MAX_SPREAD', '0.002')),
            'order_size': float(os.getenv('ORDER_SIZE', '0.01')),
            'inventory_target': float(os.getenv('INVENTORY_TARGET', '0.0')),
            'inventory_range': float(os.getenv('INVENTORY_RANGE', '0.1')),
            'risk_limit': float(os.getenv('RISK_LIMIT', '0.1')),
            'max_orders': int(os.getenv('MAX_ORDERS', '10')),
            'order_book_depth': int(os.getenv('ORDER_BOOK_DEPTH', '20')),
            'price_precision': int(os.getenv('PRICE_PRECISION', '2')),
            'size_precision': int(os.getenv('SIZE_PRECISION', '4')),
            'kappa': float(os.getenv('KAPPA', '0.1')),
            'alpha': float(os.getenv('ALPHA', '0.1')),
            'gamma': float(os.getenv('GAMMA', '0.1')),
            'sigma': float(os.getenv('SIGMA', '0.1')),
            'delta': float(os.getenv('DELTA', '0.1')),
        }
        
        logger.info("Starting market maker with configuration:")
        for key, value in config.items():
            logger.info(f"{key}: {value}")
        
        # 创建并启动做市商
        market_maker = MarketMaker(
            exchange_id=exchange_id,
            symbol=symbol,
            api_key=api_key,
            secret=secret,
            config=config
        )
        
        logger.info("Starting market maker...")
        await market_maker.start()
        
    except KeyboardInterrupt:
        logger.info("Strategy stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
    finally:
        # 确保在退出时关闭所有连接
        if 'market_maker' in locals():
            await market_maker.stop()

if __name__ == "__main__":
    try:
        # 使用asyncio运行主函数
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Strategy stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        # 关闭事件循环
        loop.close() 