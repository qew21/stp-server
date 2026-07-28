import asyncio
import base64
import hashlib
import json
import time
from typing import Dict, Any

import aiohttp
import datetime
import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from fastapi import APIRouter, Body, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from pytz import timezone

from app.internal import traderapi

logger = logging.getLogger(__name__)

from app.internal.stp import stp_client
import akshare as ak
import requests
import httpx

router = APIRouter()


async def get_json(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except Exception as e:
        logger.error(f"get_json error: {e}")
    return {}


async def login_request():
    base_url = 'http://127.0.0.1:7001'
    res = await get_json(base_url + '/login')
    logger.info(res)
    return res


async def logout_request():
    base_url = 'http://127.0.0.1:7001'
    res = await get_json(base_url + '/logout')
    logger.info(res)
    return res


@router.on_event("startup")
def before_server_start():
    '''全局共享session'''
    logger.info("before_server_start")
    global scheduler, stp_client
    scheduler = AsyncIOScheduler()
    scheduler.add_job(login_request, trigger='date',
                      next_run_time=datetime.datetime.now(timezone('Asia/Shanghai')) + datetime.timedelta(seconds=10), id="pad_task")
    scheduler.start()


@router.on_event("shutdown")
def after_server_stop():
    '''关闭session'''
    logger.info("after_server_stop")
    stp_client.logout()
    scheduler.shutdown()


@router.get('/login')
def login():
    try:
        stp_client.login()
        data = {"time": datetime.datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/logout')
def logout():
    try:
        stp_client.logout()
        return JSONResponse({"time": datetime.datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/get_account')
def get_account():
    try:
        data = stp_client.getAccount()
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/get_position')
def get_postion():
    try:
        data = stp_client.getPositions()
        price_dict = ak.stock_zh_a_spot_em().set_index("代码")["最新价"].to_dict()
        for i in data[0]:
            i['latest'] = price_dict.get(i['SecurityID'])
            i["value"] = round(i['CurrentPosition'] * i['latest'], 2)
            i["profit"] = round(i["value"] - i["TotalPosCost"], 2)
        print(data)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/order_limit')
def order_limit(code, volume=100, price=0):
    '''
    code为合约代码，direction为字符串"long"或者"short"之一，表示多头或空头。volume为整数，表示交易数量，正数表示该方向加仓，负数表示该方向减仓。price为float类型的价格。提交成功返回“订单号@合约号”。
    '''

    try:
        data = stp_client.orderInsert(code, float(price), int(volume), order_type=traderapi.TORA_TSTP_OPT_LimitPrice)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get('/order_custom')
def order_custom(code, volume, price_type, plus=0):
    '''
    code为合约代码，direction为字符串"long"或者"short"之一，表示多头或空头。volume为整数，表示交易数量，正数表示该方向加仓，负数表示该方向减仓。price为float类型的价格。提交成功返回“订单号@合约号”。
    '''

    try:
        price_data = stp_client.query_points(code)
        volume = int(volume)
        price = price_data[price_type] + int(plus) * 0.01
        data = stp_client.orderInsert(code, price, volume, order_type=traderapi.TORA_TSTP_OPT_LimitPrice)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/order_market')
def order_limit(code, volume=100, price=0):
    '''
    code为合约代码，direction为字符串"long"或者"short"之一，表示多头或空头。volume为整数，表示交易数量，正数表示该方向加仓，负数表示该方向减仓。price为float类型的价格。提交成功返回“订单号@合约号”。
    '''

    try:
        try:
            volume = int(volume)
            price_data = stp_client.query_points(code)
            limit_price = price_data['UpperLimitPrice'] if volume > 0 else price_data['LowerLimitPrice']
            # 获取最新价格确保能成交
            data = stp_client.orderInsert(code, round(limit_price, 2), volume, order_type=traderapi.TORA_TSTP_OPT_BestPrice)
        except Exception as e:
            logger.error(e)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})



@router.get('/order_delete')
def order_delete(order_id, exd='SZ'):
    '''
    已提交未完全成交的限价单可以撤单。order_id为orderLimit()的返回值。
    '''
    try:
        data = stp_client.deleteOrder(order_id, exd == 'SH')
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"status": str(e)})


@router.get('/order_status')
def order_status(order_id):
    '''
    已提交未完全成交的限价单可以撤单。order_id为orderLimit()的返回值。
    '''
    try:
        data = stp_client.getTheOrder(order_id)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"status": str(e)})

@router.get('/get_orders')
def get_orders():
    try:
        data = stp_client.getOrders()
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/get_trades')
def get_trades():
    try:
        data = stp_client.getTrades()
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/subscribe')
def subscribe(codes):
    try:
        if codes != "":
            stp_client.subscribe(codes.split(','))
            data = "已订阅{}合约".format(codes)
        else:
            data = {}
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/unsubscribe')
def unsubscribe(codes):
    try:
        if codes != "":
            stp_client.unsubscribe(codes.split(','))
            data = "已取消订阅{0}".format(codes)
        else:
            data = {}
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get('/hq')
def market_realtime_hq(code):
    '''
    行情数据：实时
    '''
    try:
        data = stp_client.query_points(code)
        return json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=bytes_encoder
        ).encode("utf-8")
    except Exception as e:
        return JSONResponse({"error": str(e)})



def bytes_encoder(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)
