#!/usr/bin/python3
# -*- coding: UTF-8 -*-


# from asyncio.windows_events import NULL #仅适用于Windows
import sys
import time

from app.internal import lev2mdapi
from app.internal.spi import SpiHelper
import logging


logger = logging.getLogger("subscribe")
''' 注意: 如果提示找不到_lev2mdapi 且已发布的库文件不一致时,可自行重命名为_lev2mdapi.so (Windows下为_lev2mdapi.pyd)'''


class QuoteImpl(SpiHelper, lev2mdapi.CTORATstpLev2MdSpi):
    def __init__(self, sh=False):
        SpiHelper.__init__(self)
        lev2mdapi.CTORATstpLev2MdSpi.__init__(self)
        self.__api = None
        self.is_sh = sh
        self.connect_status = False
        self.market_data = {}
        self.connect()

    def connect(self):
        if not self.connect_status:
            logger.info("LEV2MDAPI版本号::" + lev2mdapi.CTORATstpLev2MdApi_GetApiVersion())
            if self.is_sh:
                LEV2MD_TCP_FrontAddress = "tcp://210.14.72.17:16900"  # 深圳测试桩
            else:
                LEV2MD_TCP_FrontAddress = "tcp://210.14.72.17:6900"  # 深圳测试桩
            logger.info("************* LEV2MD TCP *************")
            self.__api = lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi()
            self.__api.RegisterFront(LEV2MD_TCP_FrontAddress)
            logger.info("LEV2MD_TCP_FrontAddress[TCP]::%s" % LEV2MD_TCP_FrontAddress)
            self.__api.RegisterSpi(self)
            self.__api.Init()
            time.sleep(0.5)
            self.connect_status = True

    def subscribe(self, codes):
        # 3s快照订阅，不含上海可转债(XTS新债)

        logger.info(f"Securities_stock: {codes}")
        ret_md = self.__api.SubscribeMarketData(codes, lev2mdapi.TORA_TSTP_EXD_SSE if self.is_sh else lev2mdapi.TORA_TSTP_EXD_SZSE)  # 深圳股票通配符查询举例
        if ret_md != 0:
            logger.info('SubscribeMarketData fail, ret[%d]' % ret_md)
        else:
            logger.info('SubscribeMarketData success, ret[%d]' % ret_md)


    def unsubscribe(self, codes):
        # 3s快照订阅，不含上海可转债(XTS新债)
        ret_md = self.__api.UnSubscribeMarketData(codes, lev2mdapi.TORA_TSTP_EXD_SSE if self.is_sh else lev2mdapi.TORA_TSTP_EXD_SZSE)  # 深圳股票通配符查询举例
        if ret_md != 0:
            logger.info('UnSubscribeMarketData fail, ret[%d]' % ret_md)
        else:
            logger.info('UnSubscribeMarketData success, ret[%d]' % ret_md)

    def OnFrontConnected(self):
        logger.info("OnFrontConnected")

        login_req = lev2mdapi.CTORATstpReqUserLoginField()
        # 使用组播方式接收行情时，Login请求域可置空，不必填写校验信息
        # 当使用TCP方式接收行情时，则必须填写校验信息：LogInAccount,Password和LogInAccountType
        ''' 
        LogInAccount为申请的手机号
        Password为该手机号在N视界网站的登陆密码。
        LogInAccountType = TORA_TSTP_LACT_UnifiedUserID
        若填入的手机号尚未登记会提示ErrorID[439]
        '''
        login_req.LogInAccount = '13811112222'  # n-sight.com.cn网站注册手机号
        login_req.Password = '123456'  # n-sight.com.cn网站登陆密码
        login_req.LogInAccountType = lev2mdapi.TORA_TSTP_LACT_UnifiedUserID  # 统一标识登陆，level2用户校验指定类型

        self.__api.ReqUserLogin(login_req, 1)

    def OnRspUserLogin(self, pRspUserLoginField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('Login success! [%d]' % nRequestID)

            #########以下为逐笔数据订阅######
            Securities = [b'00000000']  # 全部合约(通配符)
            Securities_startwith_sh = [b'6*****']  # 通配符方式
            Securities_stock_sh = [b'600036']  # 上海股票
            Securities_index_sh = [b'000905', b'000852']  # 上海指数
            Securities_cbond_sh = [b'110038', b'110043', b'113537']  # 上海可转债

            Securities_stock_sz = [b'000001', b'000650', b'300750']  # 深圳股票
            Securities_startwith_sz = [b'000***', b'3*****']  # 通配符方式
            Securities_index_sz = [b'399001']  # 深圳指数
            Securities_cbond_sz = [b'123013']  # 深圳可转债
            Securities_sz = [b'300750', b'123013']  # 深圳股票+可转债

            '''
            订阅快照行情
            当sub_arr中只有一个"00000000"的合约且ExchangeID填TORA_TSTP_EXD_SSE或TORA_TSTP_EXD_SZSE时,订阅单市场所有合约行情
			当sub_arr中只有一个"00000000"的合约且ExchangeID填TORA_TSTP_EXD_COMM时,订阅全市场所有合约行情
            支持类似 600*** 通配符,不支持 6*****1 类型通配符。
			其它情况,订阅sub_arr集合中的合约行情
            '''
            if 0:  # 3s快照订阅，不含上海可转债(XTS新债)
                # ret_md = self.__api.SubscribeMarketData(Securities_stock_sh, lev2mdapi.TORA_TSTP_EXD_SSE) #上海股票
                ret_md = self.__api.SubscribeMarketData(Securities_stock_sh,
                                                        lev2mdapi.TORA_TSTP_EXD_COMM)  # 深圳股票通配符查询举例
                # ret_md = self.__api.SubscribeMarketData(Securities_sz, lev2mdapi.TORA_TSTP_EXD_SZSE) #深圳股票+可转债
                # ret_md = self.__api.SubscribeMarketData(Securities, lev2mdapi.TORA_TSTP_EXD_COMM)  #沪深全市场订阅，不含上海可转债
                if ret_md != 0:
                    logger.info('SubscribeMarketData fail, ret[%d]' % ret_md)
                else:
                    logger.info('SubscribeMarketData success, ret[%d]' % ret_md)

            if 0:  # 指数快照订阅
                ret_i = self.__api.SubscribeIndex(Securities_index_sh, lev2mdapi.TORA_TSTP_EXD_SSE)  # 订阅上海指数
                # ret_i = self.__api.SubscribeIndex(Securities_index_sz, lev2mdapi.TORA_TSTP_EXD_SZSE)  #订阅深圳指数
                # ret_i = self.__api.SubscribeIndex(Securities, lev2mdapi.TORA_TSTP_EXD_COMM) #全市场指数订阅
                if (ret_i == 0):
                    logger.info("SubscribeIndex:::Success,ret=%d" % ret_i)
                else:
                    logger.info("SubscribeIndex:::Failed,ret=%d)" % ret_i)

            if 0:  # 逐笔成交订阅（不含上海XTS新债,但包括深圳可转债）
                ret_t = self.__api.SubscribeTransaction(Securities_stock_sh, lev2mdapi.TORA_TSTP_EXD_COMM)  # 订阅上海股票
                # ret_t = self.__api.SubscribeTransaction(Securities_sz, lev2mdapi.TORA_TSTP_EXD_SZSE)  #订阅深圳股票+可转债
                # ret_t = self.__api.SubscribeTransaction(Securities, lev2mdapi.TORA_TSTP_EXD_COMM) #全市场订阅
                if (ret_t == 0):
                    logger.info("SubscribeTransaction:::Success,ret=%d" % ret_t)
                else:
                    logger.info("SubscribeTransaction:::Failed,ret=%d)" % ret_t)

            if 0:  # 逐笔委托订阅（不含上海XTS新债,但包括深圳可转债）
                ret_od = self.__api.SubscribeOrderDetail(Securities_stock_sh, lev2mdapi.TORA_TSTP_EXD_COMM)  # 订阅上海股票
                # ret_od = self.__api.SubscribeOrderDetail(Securities_sz, lev2mdapi.TORA_TSTP_EXD_SZSE)  #订阅深圳股票+转债
                # ret_od = self.__api.SubscribeOrderDetail(Securities, lev2mdapi.TORA_TSTP_EXD_COMM) #全市场指数订阅
                if (ret_od == 0):
                    logger.info("SubscribeOrderDetail:::Success,ret=%d" % ret_od)
                else:
                    logger.info("SubscribeOrderDetail:::Failed,ret=%d)" % ret_od)

            if 0:  # 上海XTS新债快照订阅
                ret_xts_md = self.__api.SubscribeXTSMarketData(Securities_cbond_sh,
                                                               lev2mdapi.TORA_TSTP_EXD_SSE)  # 订阅上海可转债
                if (ret_xts_md == 0):
                    logger.info("SubscribeXTSMarketData:::Success,ret=%d" % ret_xts_md)
                else:
                    logger.info("SubscribeXTSMarketData:::Failed,ret=%d)" % ret_xts_md)

            if 0:  # 上海XTS新债逐笔委托和逐笔成交订阅
                ret_xts_tick = self.__api.SubscribeXTSTick(Securities_cbond_sh,
                                                           lev2mdapi.TORA_TSTP_EXD_SSE)  # 订阅上海可转债(XTS新债)
                if (ret_xts_tick == 0):
                    logger.info("SubscribeXTSTick:::Success,ret=%d" % ret_xts_tick)
                else:
                    logger.info("SubscribeXTSTick:::Failed,ret=%d)" % ret_xts_tick)

        else:  # login
            logger.error('Login fail!!! [%d] [%d] [%s]'
                  % (nRequestID, pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    ######以下为行情订阅响应########
    def OnRspSubMarketData(self, pSpecificSecurityField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubMarketData: OK!')
        else:
            logger.error('OnRspSubMarketData: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspUnSubMarketData(self, pSpecificSecurityField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            logger.info('OnRspUnSubMarketData: OK!')
        else:
            logger.error('OnRspUnSubMarketData: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspSubIndex(self, pSpecificSecurityField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubIndex: OK!')
        else:
            logger.error('OnRspSubIndex: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspSubTransaction(self, pSpecificSecurity, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubTransaction: OK!')
        else:
            logger.error('OnRspSubTransaction: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspSubOrderDetail(self, pSpecificSecurity, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubOrderDetail: OK!')
        else:
            logger.error('OnRspSubOrderDetail: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspSubXTSMarketData(self, pSpecificSecurity, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubXTSMarketData: OK!')
        else:
            logger.error('OnRspSubXTSMarketData: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    def OnRspSubXTSTick(self, pSpecificSecurity, pRspInfo, nRequestID, bIsLast):
        if pRspInfo['ErrorID'] == 0:
            logger.info('OnRspSubXTSTick: OK!')
        else:
            logger.error('OnRspSubXTSTick: Error! [%d] [%s]'
                  % (pRspInfo['ErrorID'], pRspInfo['ErrorMsg']))

    # #####以下为行情推送的回报########

    # 普通快照行情回报
    def OnRtnMarketData(self, pMarketData, FirstLevelBuyNum, FirstLevelBuyOrderVolumes, FirstLevelSellNum,
                        FirstLevelSellOrderVolumes):
        self.market_data[pMarketData['SecurityID']] = pMarketData.copy()
        logger.info(
            "OnRtnMarketData TimeStamp[%d] SecurityName[%s] ExchangeID[%s] \n\tPreClosePrice[%.4f] LowestPrice[%.4f] HighestPrice[%.4f] OpenPrice[%.4f] LastPrice[%.4f] \n\tBidPrice{[%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]} \n\tAskPrice{[%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f] [%.4f]} \n\tBidVolume{[%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld]} \n\tAskVolume{[%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld] [%ld]}\n" %
            (pMarketData['DataTimeStamp'], pMarketData['SecurityID'], pMarketData['ExchangeID'],
             pMarketData['PreClosePrice'], pMarketData['LowestPrice'],
             pMarketData['HighestPrice'], pMarketData['OpenPrice'], pMarketData['LastPrice'],
             pMarketData['BidPrice1'], pMarketData['BidPrice2'], pMarketData['BidPrice3'],
             pMarketData['BidPrice4'], pMarketData['BidPrice5'], pMarketData['BidPrice6'],
             pMarketData['BidPrice7'], pMarketData['BidPrice8'], pMarketData['BidPrice9'], pMarketData['BidPrice10'],
             pMarketData['AskPrice1'], pMarketData['AskPrice2'], pMarketData['AskPrice3'],
             pMarketData['AskPrice4'], pMarketData['AskPrice5'], pMarketData['AskPrice6'],
             pMarketData['AskPrice7'], pMarketData['AskPrice8'], pMarketData['AskPrice9'], pMarketData['AskPrice10'],
             pMarketData['BidVolume1'], pMarketData['BidVolume2'], pMarketData['BidVolume3'],
             pMarketData['BidVolume4'], pMarketData['BidVolume5'], pMarketData['BidVolume6'],
             pMarketData['BidVolume7'], pMarketData['BidVolume8'], pMarketData['BidVolume9'],
             pMarketData['BidVolume10'],
             pMarketData['AskVolume1'], pMarketData['AskVolume2'], pMarketData['AskVolume3'],
             pMarketData['AskVolume4'], pMarketData['AskVolume5'], pMarketData['AskVolume6'],
             pMarketData['AskVolume7'], pMarketData['AskVolume8'], pMarketData['AskVolume9'],
             pMarketData['AskVolume10']))

    # 指数快照行情通知
    def OnRtnIndex(self, pIndex):
        logger.info(
            "OnRtnIndex DataTimeStamp[%d] SecurityID[%s] ExchangeID[%s] LastIndex[%.4f] PreCloseIndex[%.4f] OpenIndex[%.4f] LowIndex[%.4f] HighIndex[%.4f] CloseIndex[%.4f] Turnover[%.4f] TotalVolumeTraded[%ld]" %
            (pIndex['DataTimeStamp'],  # 精确到秒，上海指数5秒一笔，深圳3秒一笔
             pIndex['SecurityID'],
             pIndex['ExchangeID'],
             pIndex['LastIndex'],
             pIndex['PreCloseIndex'],
             pIndex['OpenIndex'],
             pIndex['LowIndex'],
             pIndex['HighIndex'],
             pIndex['CloseIndex'],
             pIndex['Turnover'],
             pIndex['TotalVolumeTraded']))

    # 逐笔成交通知
    def OnRtnTransaction(self, pTransaction):
        logger.info("OnRtnTransaction SecurityID[%s] " % pTransaction['SecurityID'], end="")
        logger.info("ExchangeID[%s] " % pTransaction['ExchangeID'], end="")
        # 深圳逐笔成交，TradeTime的格式为【时分秒毫秒】例如例如100221530，表示10:02:21.530;
        # 上海逐笔成交，TradeTime的格式为【时分秒百分之秒】例如10022153，表示10:02:21.53;
        logger.info("TradeTime[%d] " % pTransaction['TradeTime'], end="")
        logger.info("TradePrice[%.4f] " % pTransaction['TradePrice'], end="")
        logger.info("TradeVolume[%ld] " % pTransaction['TradeVolume'], end="")
        logger.info("ExecType[%s] " % pTransaction['ExecType'],
              end="")  # 上海逐笔成交没有这个字段，只有深圳有。值2表示撤单成交，BuyNo和SellNo只有一个是非0值，以该非0序号去查找到的逐笔委托即为被撤单的委托。
        logger.info("MainSeq[%d] " % pTransaction['MainSeq'], end="")
        logger.info("SubSeq[%ld] " % pTransaction['SubSeq'], end="")
        logger.info("BuyNo[%ld] " % pTransaction['BuyNo'], end="")
        logger.info("SellNo[%ld] " % pTransaction['SellNo'], end="")
        logger.info("TradeBSFlag[%s] " % pTransaction['TradeBSFlag'], end="")
        logger.info("Info1[%ld] " % pTransaction['Info1'], end="")
        logger.info("Info2[%ld] " % pTransaction['Info2'], end="")
        logger.info("Info3[%ld] " % pTransaction['Info3'])

    # 逐笔委托通知
    def OnRtnOrderDetail(self, pOrderDetail):
        logger.info("OnRtnOrderDetail SecurityID[%s] " % pOrderDetail['SecurityID'], end="")
        logger.info("ExchangeID[%s] " % pOrderDetail['ExchangeID'], end="")
        logger.info("OrderTime[%d] " % pOrderDetail['OrderTime'], end="")
        logger.info("Price[%.4f] " % pOrderDetail['Price'], end="")
        logger.info("Volume[%ld] " % pOrderDetail['Volume'], end="")
        logger.info("OrderType[%s] " % pOrderDetail['OrderType'], end="")
        logger.info("MainSeq[%d] " % pOrderDetail['MainSeq'], end="")
        logger.info("SubSeq[%d] " % pOrderDetail['SubSeq'], end="")
        logger.info("Side[%s] " % pOrderDetail['Side'], end="")
        logger.info("Info1[%d] " % pOrderDetail['Info1'], end="")
        logger.info("Info2[%d] " % pOrderDetail['Info2'], end="")
        logger.info("Info3[%d] " % pOrderDetail['Info3'])

    def OnRtnXTSMarketData(self, pMarketData, FirstLevelBuyNum, FirstLevelBuyOrderVolumes, FirstLevelSellNum,
                           FirstLevelSellOrderVolumes):
        if (pMarketData):
            logger.info("OnRtnXTSMarketData SecurityID[%s] " % pMarketData['SecurityID'], end="")
            logger.info("ExchangeID[%s] " % pMarketData['ExchangeID'], end="")
            logger.info("DataTimeStamp[%d] " % pMarketData['DataTimeStamp'], end="")
            logger.info("PreClosePrice[%.4f] " % pMarketData['PreClosePrice'], end="")
            logger.info("OpenPrice[%.4f] " % pMarketData['OpenPrice'], end="")
            logger.info("NumTrades[%ld] " % pMarketData['NumTrades'], end="")
            logger.info("TotalVolumeTrade[%ld] " % pMarketData['TotalVolumeTrade'], end="")
            logger.info("HighestPrice[%.4f] " % pMarketData['HighestPrice'], end="")
            logger.info("LowestPrice[%.4f] " % pMarketData['LowestPrice'], end="")
            logger.info("LastPrice[%.4f] " % pMarketData['LastPrice'], end="")
            logger.info("BidPrice1[%.4f] " % pMarketData['BidPrice1'], end="")
            logger.info("BidVolume1[%ld] " % pMarketData['BidVolume1'], end="")
            logger.info("AskPrice1[%.4f] " % pMarketData['AskPrice1'], end="")
            logger.info("AskVolume1[%ld] " % pMarketData['AskVolume1'], end="")
            logger.info("MDSecurityStat[%s] " % pMarketData['MDSecurityStat'])

    # 上海可转债XTS债券逐笔数据通知
    def OnRtnXTSTick(self, pTick):
        logger.info("OnRtnXTSTick SecurityID[%s] " % pTick['SecurityID'], end="")
        logger.info("ExchangeID[%s] " % pTick['ExchangeID'], end="")
        logger.info("MainSeq[%d] " % pTick['MainSeq'], end="")
        logger.info("SubSeq[%ld] " % pTick['SubSeq'], end="")
        logger.info("TickTime[%d] " % pTick['TickTime'], end="")
        logger.info("TickType[%s] " % pTick['TickType'], end="")
        logger.info("BuyNo[%ld] " % pTick['BuyNo'], end="")
        logger.info("SellNo[%ld] " % pTick['SellNo'], end="")
        logger.info("Price[%.4f] " % pTick['Price'], end="")
        logger.info("Volume[%ld] " % pTick['Volume'], end="")
        logger.info("TradeMoney[%.4f] " % pTick['TradeMoney'], end="")
        logger.info("Side[%s] " % pTick['Side'], end="")
        logger.info("TradeBSFlag[%s] " % pTick['TradeBSFlag'], end="")
        logger.info("MDSecurityStat[%s] " % pTick['MDSecurityStat'], end="")
        logger.info("Info1[%d] " % pTick['Info1'], end="")
        logger.info("Info2[%d] " % pTick['Info2'], end="")
        logger.info("Info3[%d] " % pTick['Info3'])

    def OnRtnBondMarketData(self, pMarketData, FirstLevelBuyNum, FirstLevelBuyOrderVolumes, FirstLevelSellNum,
                            FirstLevelSellOrderVolumes):
        logger.info("OnRtnBondMarketData::深圳普通债券（不包括可转债）快照行情")

    def OnRtnBondTransaction(self, pTransaction):
        logger.info("OnRtnBondTransaction::深圳普通债券（不包括可转债）逐笔成交")

    def OnRtnBondOrderDetail(self, pOrderDetail):
        logger.info("OnRtnBondOrderDetail::深圳普通债券（不包括可转债）逐笔委托")


if __name__ == "__main__":
    # 打印接口版本号
    logger.info("LEV2MDAPI版本号::" + lev2mdapi.CTORATstpLev2MdApi_GetApiVersion())
    argc = len(sys.argv)

    if argc == 1:  # 默认TCP连接仿真环境
        # LEV2MD_TCP_FrontAddress ="tcp://210.14.72.17:16900" #上海测试桩
        LEV2MD_TCP_FrontAddress = "tcp://210.14.72.17:6900"  # 深圳测试桩

    elif argc == 3 and sys.argv[1] == "tcp":  # 普通TCP方式
        LEV2MD_TCP_FrontAddress = sys.argv[2]
    elif argc == 4 and sys.argv[1] == "udp":  # UDP 组播
        LEV2MD_MCAST_FrontAddress = sys.argv[2]  # 组播地址
        LEV2MD_MCAST_InterfaceIP = sys.argv[3]  # 组播接收地址
    else:
        logger.info("/*********************************************demo运行说明************************************\n")
        logger.info("* argv[1]: tcp udp\t\t\t\t=[%s]" % (sys.argv[1]))
        logger.info("* argv[2]: tcp::FrontIP udp::MCAST_IP\t\t=[%s]" % (sys.argv[2] if argc > 2 else ""))
        logger.info("* argv[3]: udp::InterfaceIP\t=[%s]" % (sys.argv[3] if argc > 3 else ""))
        logger.info("* Usage:")
        logger.info("* 默认连上海测试桩:	python3 lev2mddemo.py")
        logger.info("* 指定TCP地址:		python3 lev2mddemo.py tcp tcp://210.14.72.17:16900")
        logger.info("* 指定组播地址:		python3 lev2mddemo.py udp udp://224.224.224.15:7889 10.168.9.46")
        logger.info("* 上述x.x.x.x使用托管服务器中接收LEV2MD行情的网口IP地址")
        logger.info("* ******************************************************************************************/")
        exit(-1)

    '''*************************创建实例 注册服务*****************'''
    if argc == 1 or sys.argv[1] == "tcp":  # 默认或TCP方式
        logger.info("************* LEV2MD TCP *************")
        # TCP订阅lv2行情，前置Front和FENS方式都用默认构造
        api = lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi()
        # 默认 api = lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_TCP)
        '''
        非缓存模式: lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_TCP,false)
        缓存模式：  lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_TCP,true)
        非缓存模式相比缓存模式处理效率更高,但回调处理逻辑耗时长可能导致连接中断时,建议使用缓存模式
        '''

        api.RegisterFront(LEV2MD_TCP_FrontAddress)
        # 注册多个行情前置服务地址，用逗号隔开
        # 例如:api.RegisterFront("tcp://10.0.1.101:6402,tcp://10.0.1.101:16402")
        logger.info("LEV2MD_TCP_FrontAddress[TCP]::%s" % LEV2MD_TCP_FrontAddress)

    elif sys.argv[1] == "udp":  # 组播普通行情
        logger.info("************* LEV2MD UDP *************")
        # LEV2MD组播订阅lv2行情，默认非缓存模式
        api = lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_MCAST)
        '''
        非缓存模式: lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_MCAST,false)
        缓存模式：  lev2mdapi.CTORATstpLev2MdApi_CreateTstpLev2MdApi(lev2mdapi.TORA_TSTP_MST_MCAST,true)
        非缓存模式相比缓存模式处理效率更高,但回调处理逻辑耗时长可能导致不能完整及时处理数据时,建议使用缓存模式
        '''
        api.RegisterMulticast(LEV2MD_MCAST_FrontAddress, LEV2MD_MCAST_InterfaceIP, "")
        logger.info("LEV2MD_MCAST_FrontAddress[UDP]::%s" % LEV2MD_MCAST_FrontAddress)
        logger.info("LEV2MD_MCAST_InterfaceIP::%s" % LEV2MD_MCAST_InterfaceIP)

    else:
        logger.info("/*********************************************demo运行说明************************************\n")
        logger.info("* argv[1]: tcp udp\t\t\t\t=[%s]" % (sys.argv[1]))
        logger.info("* argv[2]: tcp::FrontIP udp::MCAST_IP\t\t=[%s]" % (sys.argv[2] if argc > 2 else ""))
        logger.info("* argv[3]: udp::InterfaceIP\t=[%s]" % (sys.argv[3] if argc > 3 else ""))
        logger.info("* Usage:")
        logger.info("* 默认连上海测试桩:	python3 lev2mddemo.py")
        logger.info("* 指定TCP地址:		python3 lev2mddemo.py tcp tcp://210.14.72.17:16900")
        logger.info("* 指定组播地址:		python3 lev2mddemo.py udp udp://224.224.224.15:7889 10.168.9.46")
        logger.info("* 上述x.x.x.x使用托管服务器中接收LEV2MD行情的网口IP地址")
        logger.info("* ******************************************************************************************/")
        sys.exit(-2)

    # 创建回调对象
    spi = QuoteImpl(api)

    # 注册回调接口
    api.RegisterSpi(spi)

    # 启动接口,不输入参数时为不绑核运行
    api.Init()
    # 绑核运行需要输入核心编号.
    # TCP模式收取行情时，非缓存模式1个线程,缓存模式2个线程,相应绑几个核心即可
    # 组播模式收取行情时，需要传递的核的数目= 注册的组播地址数目+[缓存模式? 1: 0]
    # 平台服务器PROXY模式时,线程数2,绑定不低于2个核心
    # api.Init("2,17")

    # 等待程序结束
    input()

    # 释放接口对象
    api.Release()
