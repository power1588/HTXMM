# HTX CCXT Market Maker

基于CCXT Pro的HTX交易所做市商策略实现。

## 功能特点

- 使用CCXT Pro进行异步交易
- 支持HTX永续合约交易
- 实现AS2008做市商策略
- 完整的风险管理和订单管理
- 实时市场数据订阅

## 环境要求

- Python 3.10+
- CCXT >= 4.1.13
- 其他依赖见requirements.txt

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/power1588/HTXMM.git
cd HTXMM
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 复制示例配置文件：
```bash
cp config.env.example config.env
```

2. 编辑config.env文件，填入你的HTX API密钥：
```
EXCHANGE_ID=htx
SYMBOL=ETH/USDT:USDT
API_KEY=your_api_key
SECRET=your_secret
```

## 运行

```bash
python run_strategy.py
```

## API测试

项目包含完整的API测试套件，可以测试HTX永续合约API的功能：

1. 确保已设置环境变量：
```bash
export HTX_API_KEY=your_api_key
export HTX_SECRET_KEY=your_secret
```

2. 运行测试：
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_htx_api_live.py::test_place_eth_order_at_1790 -v
```

测试包括：
- 公共接口测试（合约信息、深度数据、K线数据）
- 账户和持仓信息测试
- 订单操作测试（下单、查询、撤单）

## 配置参数

- `order_update_interval`: 订单更新间隔(秒)
- `max_position`: 最大持仓量
- `min_spread`: 最小价差
- `max_spread`: 最大价差
- `order_size`: 订单大小
- `inventory_target`: 目标库存
- `inventory_range`: 库存范围
- `risk_limit`: 风险限制
- `max_orders`: 最大订单数
- `order_book_depth`: 订单簿深度
- `price_precision`: 价格精度
- `size_precision`: 数量精度
- `kappa`: 库存调整系数
- `alpha`: 价格调整系数
- `gamma`: 风险调整系数
- `sigma`: 波动率系数
- `delta`: 时间衰减系数

## 日志

日志文件保存在`logs`目录下，格式为`market_maker_YYYYMMDD_HHMMSS.log`。

## 注意事项

- 请确保API密钥有足够的权限
- 建议先在测试环境中运行
- 注意控制风险参数
- 定期检查日志文件

## 贡献

欢迎提交Issue和Pull Request。

## 许可证

MIT License