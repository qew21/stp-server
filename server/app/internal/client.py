import datetime
import time
from copy import deepcopy
import logging

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from app.internal.spi import SpiHelper
from app.internal.quote1 import QuoteImpl
from app.internal.trader import TraderSpi


logger = logging.getLogger(__name__)
subscribe_logger = logging.getLogger('subscribe')


class Client:
    def __init__(self):
        self._md = None
        self._md_sh = None
        self._td = None
        self.quotes = {}
        self.subscribe_codes = []
        self.price_change_time = time.time()
        self.last_update = datetime.datetime.now() - datetime.timedelta(seconds=1000)

    def login(self):
        '''
        登录行情、交易
        '''
        self._td = None
        self._td = TraderSpi()
        self._md = None
        self._md = QuoteImpl()
        self.subscribe_codes = []

    def logout(self):
        '''
        登出
        '''
        # self._md.shutdown()
        self._td.logout()
        self.subscribe_codes = []


    def subscribe_l2(self, codes):
        '''
        订阅合约代码
        '''
        if not self._td:
            return '账户未登陆！'
        Securities_stock_sz = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SZ']
        Securities_stock_sh = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SH']
        if Securities_stock_sz:
            self.subscribe_codes.extend(Securities_stock_sz)
            self._md.subscribe(Securities_stock_sz)
        if Securities_stock_sh:
            self.subscribe_codes.extend(Securities_stock_sz)
            self._md_sh.subscribe(Securities_stock_sh)

    def subscribe(self, codes):
        '''
        订阅合约代码
        '''
        if not self._td:
            return '账户未登陆！'
        if not self._td:
            return '账户未登陆！'
        Securities_stock_sz = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SZ']
        Securities_stock_sh = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SH']
        if Securities_stock_sz:
            self.subscribe_codes.extend(Securities_stock_sz)
            self._md.subscribe(Securities_stock_sz, is_sh=False)
        if Securities_stock_sh:
            self.subscribe_codes.extend(Securities_stock_sz)
            self._md.subscribe(Securities_stock_sh, is_sh=True)

    def get_instruments_option(self, future=None):
        '''
        获取期权合约列表，可指定对应的期货代码
        '''
        if not self._td:
            return '账户未登陆！'
        if future is None:
            return self._td.instruments_option
        return self._td.instruments_option.get(future, None)

    def get_instruments_future(self, exchange=None):
        '''
        获取期货合约列表，可指定对应的交易所
        '''
        if not self._td:
            return '账户未登陆！'
        if exchange is None:
            return self._td.instruments_future
        return self._td.instruments_future[exchange]

    def unsubscribe(self, codes):
        '''
        取消订阅
        '''
        Securities_stock_sz = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SZ']
        Securities_stock_sh = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SH']
        if Securities_stock_sz:
            for i in Securities_stock_sz:
                if i in self.subscribe_codes:
                    self.subscribe_codes.remove(i)
            self._md.unsubscribe(Securities_stock_sz, is_sh=False)
        if Securities_stock_sh:
            for i in Securities_stock_sh:
                if i in self.subscribe_codes:
                    self.subscribe_codes.remove(i)
            self._md.unsubscribe(Securities_stock_sh, is_sh=True)

    def unsubscribe_l2(self, codes):
        '''
        取消订阅
        '''
        Securities_stock_sz = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SZ']
        Securities_stock_sh = [bytes(code[2:], encoding='utf-8') for code in codes if code[:2] == 'SH']
        if Securities_stock_sz:
            for i in Securities_stock_sz:
                if i in self.subscribe_codes:
                    self.subscribe_codes.remove(i)
            self._md.unsubscribe(Securities_stock_sz)
        if Securities_stock_sh:
            for i in Securities_stock_sh:
                if i in self.subscribe_codes:
                    self.subscribe_codes.remove(i)
            self._md_sh.unsubscribe(Securities_stock_sh)

    def getInstrument(self, code):
        '''
        获取指定合约详情
        '''
        try:
            if not self._td:
                return '账户未登陆！'
            if code not in self._td._instruments:
                raise ValueError("合约<%s>不存在" % code)
            return self._td._instruments[code].copy()
        except Exception as e:
            logger.error(e)
            return {}

    def getAccount(self):
        '''
        获取账号资金情况
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getAccount()

    def getQuote(self, code):
        '''
        获取账号资金情况
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getQuote(code)

    def getOrders(self):
        '''
        获取当天订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getOrders()

    def getTheOrder(self, sys_id):
        '''
        获取当天订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getTheOrder(sys_id)

    def getTrades(self):
        '''
        获取当天订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.getTrades()

    def getPositions(self):
        '''
        获取持仓
        '''
        if not self._td:
            return '账户未登陆！'
        data = self._td.getPositions()
        return data


    def orderMarket(self, code, direction, volume, target_price_type, offset_flag=None):
        '''
        市价下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderMarket(code, direction, volume, target_price_type, offset_flag)

    def orderFAK(self, code, direction, volume, price, min_volume):
        '''
        FAK下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderFAK(code, direction, volume, price, min_volume)

    def orderFOK(self, code, direction, volume, price):
        '''
        FOK下单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderFOK(code, direction, volume, price)

    def orderLimit(self, code, direction, volume, price, offset_flag=None):
        '''
        限价单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderLimit(code, direction, volume, price, offset_flag)

    def orderInsert(self, code, price, volume, order_type):
        '''
                限价单
                '''
        if not self._td:
            return '账户未登陆！'
        return self._td.orderInsert(code, price, volume, order_type)


    def deleteOrder(self, order_id, is_sse):
        '''
        撤销订单
        '''
        if not self._td:
            return '账户未登陆！'
        return self._td.deleteOrder(order_id, is_sse)


    @staticmethod
    def is_trade_time():
        # 判断是否在交易时间
        now = datetime.datetime.now(timezone('Asia/Shanghai'))
        # 如果不是周一到周五
        if now.weekday() >= 5:
            return False
        # 9:30 - 11:30 13:00 - 15:00 21:00 - 23:00
        if (now.hour == 9 and now.minute >= 30) or (now.hour == 10) or (now.hour == 11 and now.minute <= 30) or \
                (now.hour == 13) or (now.hour == 14) or (now.hour == 15 and now.minute <= 30) or \
                (now.hour == 21) or (now.hour == 22) or (now.hour == 23 and now.minute <= 30):
            return True
        return False

    def query_points(self, code):
        # 查询合约点数的方法
        logger.debug(f"query points for {code}")
        try:
            if not self._md:
                logger.error("market data not connected")
                return None
            short_code = code[2:]
            md = self._md
            data = md.market_data.get(short_code)
            if data:
                return data
            if code not in self.subscribe_codes:
                self.subscribe([code])
            else:
                logger.debug(f"already subscribed {code}")
            start = time.time()
            # 超时5秒
            while time.time() - start < 5:
                if md.market_data.get(short_code):
                    data = deepcopy(md.market_data[short_code])
                    break
                time.sleep(0.1)
            logger.debug(f"get points for {code} done with {data}")
            return data
        except Exception as e:
            logger.error(e)
            return None
