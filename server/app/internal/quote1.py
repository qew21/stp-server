#!/usr/bin/python3
# -*- coding: UTF-8 -*-


# from asyncio.windows_events import NULL #仅适用于Windows
import sys
import time

from app.config import account
from app.internal import xmdapi
from app.internal.spi import SpiHelper
import logging


logger = logging.getLogger("subscribe")
''' 注意: 如果提示找不到_xmdapi 且已发布的库文件不一致时,可自行重命名为_xmdapi.so (Windows下为_xmdapi.pyd)'''


class QuoteImpl(SpiHelper, xmdapi.CTORATstpXMdSpi):
    def __init__(self):
        SpiHelper.__init__(self)
        xmdapi.CTORATstpXMdSpi.__init__(self)
        self.__api = None
        self.connect_status = False
        self.market_data = {}
        self.connect()

    def connect(self):
        if not self.connect_status:
            logger.info("xmdapi版本号::" + xmdapi.CTORATstpXMdApi_GetApiVersion())
            logger.info("************* LEV2MD TCP *************")
            self.__api = xmdapi.CTORATstpXMdApi_CreateTstpXMdApi()
            self.__api.RegisterFront(account.md_server)
            logger.info("LEV2MD_TCP_FrontAddress[TCP]::%s" % account.md_server)
            self.__api.RegisterSpi(self)
            self.__api.Init()
            time.sleep(0.5)
            self.connect_status = True

    def subscribe(self, codes, is_sh=False):
        # 3s快照订阅，不含上海可转债(XTS新债)
        logger.info(f"Securities_stock: {codes} , is_sh:{is_sh}")
        print(f"Securities_stock: {codes} , is_sh:{is_sh}")
        ret_md = self.__api.SubscribeMarketData(codes, xmdapi.TORA_TSTP_EXD_SSE if is_sh else xmdapi.TORA_TSTP_EXD_SZSE)  # 深圳股票通配符查询举例
        if ret_md != 0:
            logger.info('SubscribeMarketData fail, ret[%d]' % ret_md)
        else:
            logger.info('SubscribeMarketData success, ret[%d]' % ret_md)

    def unsubscribe(self, codes, is_sh=False):
        # 3s快照订阅，不含上海可转债(XTS新债)
        ret_md = self.__api.UnSubscribeMarketData(codes, xmdapi.TORA_TSTP_EXD_SSE if is_sh else xmdapi.TORA_TSTP_EXD_SZSE)  # 深圳股票通配符查询举例
        if ret_md != 0:
            logger.info('UnSubscribeMarketData fail, ret[%d]' % ret_md)
        else:
            logger.info('UnSubscribeMarketData success, ret[%d]' % ret_md)

    def OnFrontConnected(self):
        logger.info("OnFrontConnected")

        login_req = xmdapi.CTORATstpReqUserLoginField()
        # 请求登录，目前未校验登录用户，请求域置空即可
        self.__api.ReqUserLogin(login_req, 1)

    def OnRspUserLogin(self, pRspUserLoginField, pRspInfoField, nRequestID):
        logger.info(f"OnRspUserLogin {pRspInfoField.ErrorID}")
        if pRspInfoField.ErrorID == 0:
            logger.info('Login success! [%d]' % nRequestID)

            '''
            订阅行情
            当sub_arr中只有一个"00000000"的合约且ExchangeID填TORA_TSTP_EXD_SSE或TORA_TSTP_EXD_SZSE时，订阅单市场所有合约行情
            当sub_arr中只有一个"00000000"的合约且ExchangeID填TORA_TSTP_EXD_COMM时，订阅全市场所有合约行情
            其它情况，订阅sub_arr集合中的合约行情
            '''
            sub_arr = [b'600004']
            ret = self.__api.SubscribeMarketData(sub_arr, xmdapi.TORA_TSTP_EXD_SSE)
            if ret != 0:
                logger.info('SubscribeMarketData fail, ret[%d]' % ret)
            else:
                logger.info('SubscribeMarketData success, ret[%d]' % ret)

            sub_arr = [b'600004']
            ret = self.__api.UnSubscribeMarketData(sub_arr, xmdapi.TORA_TSTP_EXD_SSE)
            if ret != 0:
                logger.info('UnSubscribeMarketData fail, ret[%d]' % ret)
            else:
                logger.info('SubscribeMarketData success, ret[%d]' % ret)


        else:
            logger.info('Login fail!!! [%d] [%d] [%s]'
                  % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRspSubMarketData(self, pSpecificSecurityField, pRspInfoField):
        if pRspInfoField.ErrorID == 0:
            logger.info('OnRspSubMarketData: OK!')
        else:
            logger.info('OnRspSubMarketData: Error! [%d] [%s]'
                  % (pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRspUnSubMarketData(self, pSpecificSecurityField, pRspInfoField):
        if pRspInfoField.ErrorID == 0:
            logger.info('OnRspUnSubMarketData: OK!')
        else:
            logger.info('OnRspUnSubMarketData: Error! [%d] [%s]'
                  % (pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRtnMarketData(self, pMarketDataField):
        for attr_name in dir(pMarketDataField):
            if not attr_name.startswith("__"):
                attr_value = getattr(pMarketDataField, attr_name)
                if type(attr_value) == float:
                    setattr(pMarketDataField, attr_name, round(attr_value, 2))
        self.market_data[pMarketDataField.SecurityID] = {
            "SecurityID": pMarketDataField.SecurityID,
            "SecurityName": pMarketDataField.SecurityName,
            "LastPrice": pMarketDataField.LastPrice,
            "Volume": pMarketDataField.Volume,
            "Turnover": pMarketDataField.Turnover,
            "BidPrice1": pMarketDataField.BidPrice1,
            "BidVolume1": pMarketDataField.BidVolume1,
            "AskPrice1": pMarketDataField.AskPrice1,
            "AskVolume1": pMarketDataField.AskVolume1,
            "BidPrice2": pMarketDataField.BidPrice2,
            "BidVolume2": pMarketDataField.BidVolume2,
            "AskPrice2": pMarketDataField.AskPrice2,
            "AskVolume2": pMarketDataField.AskVolume2,
            "BidPrice3": pMarketDataField.BidPrice3,
            "BidVolume3": pMarketDataField.BidVolume3,
            "AskPrice3": pMarketDataField.AskPrice3,
            "AskVolume3": pMarketDataField.AskVolume3,
            "BidPrice4": pMarketDataField.BidPrice4,
            "BidVolume4": pMarketDataField.BidVolume4,
            "AskPrice4": pMarketDataField.AskPrice4,
            "AskVolume4": pMarketDataField.AskVolume4,
            "BidPrice5": pMarketDataField.BidPrice5,
            "BidVolume5": pMarketDataField.BidVolume5,
            "AskPrice5": pMarketDataField.AskPrice5,
            "AskVolume5": pMarketDataField.AskVolume5,
            "UpperLimitPrice": pMarketDataField.UpperLimitPrice,
            "LowerLimitPrice": pMarketDataField.LowerLimitPrice
        }
        logger.info(
            "SecurityID[%s] SecurityName[%s] LastPrice[%.2f] Volume[%d] Turnover[%.2f] BidPrice1[%.2f] BidVolume1[%d] AskPrice1[%.2f] AskVolume1[%d] UpperLimitPrice[%.2f] LowerLimitPrice[%.2f]"
            % (pMarketDataField.SecurityID, pMarketDataField.SecurityName, pMarketDataField.LastPrice,
               pMarketDataField.Volume,
               pMarketDataField.Turnover, pMarketDataField.BidPrice1, pMarketDataField.BidVolume1,
               pMarketDataField.AskPrice1,
               pMarketDataField.AskVolume1, pMarketDataField.UpperLimitPrice, pMarketDataField.LowerLimitPrice))



if __name__ == "__main__":
    # 打印接口版本号
    argc = len(sys.argv)
    logger.info(xmdapi.CTORATstpXMdApi_GetApiVersion())
    LEV2MD_TCP_FrontAddress = "tcp://210.14.72.16:9402"  # 深圳测试桩
    # 创建回调对象
    spi = QuoteImpl()
    # 注册回调接口
    spi.connect()
    time.sleep(0.5)
    input()
