# -*- coding: utf-8 -*-

import pytest
import asyncio
import json
from unittest.mock import Mock, patch
from pytest_asyncio import fixture
from exchange.htx_api import HTXLinearSwapAPI

# 测试数据
TEST_API_KEY = "test_api_key"
TEST_SECRET_KEY = "test_secret_key"
TEST_CONTRACT_CODE = "ETH-USDT"

# 模拟响应数据
MOCK_CONTRACT_INFO = {
    "status": "ok",
    "data": [{
        "symbol": "ETH",
        "contract_code": "ETH-USDT",
        "contract_size": 0.1,
        "price_tick": 0.1,
        "delivery_date": "20250101",
        "create_date": "20240101",
        "contract_status": 1
    }]
}

MOCK_MARKET_DEPTH = {
    "status": "ok",
    "tick": {
        "bids": [[2000.0, 1.0], [1999.0, 2.0]],
        "asks": [[2001.0, 1.0], [2002.0, 2.0]]
    }
}

MOCK_ACCOUNT_INFO = {
    "status": "ok",
    "data": [{
        "symbol": "USDT",
        "margin_balance": 10000.0,
        "margin_position": 1000.0,
        "margin_frozen": 0.0,
        "margin_available": 9000.0
    }]
}

@fixture
async def api():
    """创建API实例的fixture"""
    api = HTXLinearSwapAPI(TEST_API_KEY, TEST_SECRET_KEY)
    await api.init()
    yield api
    await api.close()

async def async_return(result):
    """创建一个异步返回值"""
    return result

@pytest.mark.asyncio
async def test_get_contract_info(api):
    """测试获取合约信息"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.json = Mock(side_effect=lambda: async_return(MOCK_CONTRACT_INFO))
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await api.get_contract_info(TEST_CONTRACT_CODE)
        assert result == MOCK_CONTRACT_INFO
        assert result['status'] == 'ok'
        assert len(result['data']) > 0
        assert result['data'][0]['contract_code'] == TEST_CONTRACT_CODE

@pytest.mark.asyncio
async def test_get_market_depth(api):
    """测试获取市场深度"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.json = Mock(side_effect=lambda: async_return(MOCK_MARKET_DEPTH))
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await api.get_market_depth(TEST_CONTRACT_CODE)
        assert result == MOCK_MARKET_DEPTH
        assert result['status'] == 'ok'
        assert 'tick' in result
        assert 'bids' in result['tick']
        assert 'asks' in result['tick']

@pytest.mark.asyncio
async def test_get_account_info(api):
    """测试获取账户信息"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = Mock()
        mock_response.json = Mock(side_effect=lambda: async_return(MOCK_ACCOUNT_INFO))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await api.get_account_info()
        assert result == MOCK_ACCOUNT_INFO
        assert result['status'] == 'ok'
        assert len(result['data']) > 0
        assert 'margin_balance' in result['data'][0]

@pytest.mark.asyncio
async def test_place_order(api):
    """测试下单"""
    mock_response = {
        "status": "ok",
        "data": {
            "order_id": "123456789",
            "client_order_id": "test123"
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = Mock()
        mock_resp.json = Mock(side_effect=lambda: async_return(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await api.place_order(
            contract_code=TEST_CONTRACT_CODE,
            direction="buy",
            offset="open",
            price=2000.0,
            volume=1
        )
        
        assert result == mock_response
        assert result['status'] == 'ok'
        assert 'order_id' in result['data']

@pytest.mark.asyncio
async def test_cancel_order(api):
    """测试撤单"""
    mock_response = {
        "status": "ok",
        "data": {
            "order_id": "123456789",
            "client_order_id": "test123"
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = Mock()
        mock_resp.json = Mock(side_effect=lambda: async_return(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await api.cancel_order(
            contract_code=TEST_CONTRACT_CODE,
            order_id="123456789"
        )
        
        assert result == mock_response
        assert result['status'] == 'ok'
        assert 'order_id' in result['data']

@pytest.mark.asyncio
async def test_get_order_info(api):
    """测试获取订单信息"""
    mock_response = {
        "status": "ok",
        "data": {
            "order_id": "123456789",
            "contract_code": TEST_CONTRACT_CODE,
            "direction": "buy",
            "offset": "open",
            "price": 2000.0,
            "volume": 1,
            "status": 3
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = Mock()
        mock_resp.json = Mock(side_effect=lambda: async_return(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await api.get_order_info(
            contract_code=TEST_CONTRACT_CODE,
            order_id="123456789"
        )
        
        assert result == mock_response
        assert result['status'] == 'ok'
        assert result['data']['order_id'] == "123456789"
        assert result['data']['contract_code'] == TEST_CONTRACT_CODE

@pytest.mark.asyncio
async def test_get_open_orders(api):
    """测试获取未成交订单"""
    mock_response = {
        "status": "ok",
        "data": {
            "orders": [{
                "order_id": "123456789",
                "contract_code": TEST_CONTRACT_CODE,
                "direction": "buy",
                "offset": "open",
                "price": 2000.0,
                "volume": 1,
                "status": 3
            }],
            "total_page": 1,
            "current_page": 1,
            "total_size": 1
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = Mock()
        mock_resp.json = Mock(side_effect=lambda: async_return(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await api.get_open_orders(TEST_CONTRACT_CODE)
        
        assert result == mock_response
        assert result['status'] == 'ok'
        assert len(result['data']['orders']) > 0
        assert result['data']['orders'][0]['contract_code'] == TEST_CONTRACT_CODE

@pytest.mark.asyncio
async def test_get_order_history(api):
    """测试获取历史订单"""
    mock_response = {
        "status": "ok",
        "data": {
            "orders": [{
                "order_id": "123456789",
                "contract_code": TEST_CONTRACT_CODE,
                "direction": "buy",
                "offset": "open",
                "price": 2000.0,
                "volume": 1,
                "status": 6
            }],
            "total_page": 1,
            "current_page": 1,
            "total_size": 1
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = Mock()
        mock_resp.json = Mock(side_effect=lambda: async_return(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        result = await api.get_order_history(TEST_CONTRACT_CODE)
        
        assert result == mock_response
        assert result['status'] == 'ok'
        assert len(result['data']['orders']) > 0
        assert result['data']['orders'][0]['contract_code'] == TEST_CONTRACT_CODE 