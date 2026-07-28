#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import time
import threading

from pytz import timezone

from app.internal import traderapi
from app.internal.spi import SpiHelper
from app.config import account
import logging


logger = logging.getLogger(__name__)

''' 注意: 如果提示找不到_tradeapi 且与已发布的库文件不一致时,可自行重命名为_tradeapi.so (windows下为_tradeapi.pyd)'''


class TraderSpi(SpiHelper, traderapi.CTORATstpTraderSpi):
    def __init__(self):
        SpiHelper.__init__(self)
        traderapi.CTORATstpTraderSpi.__init__(self)
        self.api: traderapi.CTORATstpTraderApi.CreateTstpTraderApi = None
        self.__req_id = 0
        self.__front_id = 0
        self.__session_id = 0
        self._last_query_time = 0
        self.InvestorID = account.InvestorID
        self.UserID = account.UserID
        self.Password = account.Password
        self.AccountID = account.AccountID
        self.DepartmentID = account.DepartmentID
        self.SSE_ShareHolderID = account.SSE_ShareHolderID
        self.SZ_ShareHolderID = account.SZ_ShareHolderID
        self.connect_status = False
        self.lastDataTime = None
        self.lastAccount = None
        self.lastPositions = []
        self.lastOrders = {}
        self.lastTrades = {}
        self.connect()

    def connect(self):
        if not self.connect_status:
            logger.info("TradeAPI Version:::" + traderapi.CTORATstpTraderApi_GetApiVersion())
            self.api = traderapi.CTORATstpTraderApi.CreateTstpTraderApi()
            self.api.RegisterSpi(self)
            TD_TCP_FrontAddress = account.trader_server  # 仿真交易环境
            self.api.RegisterFront(TD_TCP_FrontAddress)
            logger.info("TD_TCP_FensAddress[sim or 24H]::%s\n" % TD_TCP_FrontAddress)
            self.api.SubscribePrivateTopic(traderapi.TORA_TERT_QUICK)
            # 订阅公有流
            self.api.SubscribePublicTopic(traderapi.TORA_TERT_QUICK)
            self.api.Init()
            time.sleep(1)
            # self.api.Join()
            self.connect_status = True

    def OnFrontConnected(self) -> "void":
        logger.info('OnFrontConnected')

        # 获取终端信息
        self.__req_id += 1
        ret = self.api.ReqGetConnectionInfo(self.__req_id)
        if ret != 0:
            logger.info('ReqGetConnectionInfo fail, ret[%d]' % ret)

    def OnFrontDisconnected(self, nReason: "int") -> "void":
        logger.info('OnFrontDisconnected: [%d]' % nReason)

    def OnRspGetConnectionInfo(self, pConnectionInfoField: "CTORATstpConnectionInfoField",
                               pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        if pRspInfoField.ErrorID == 0:
            logger.info('inner_ip_address[%s]' % pConnectionInfoField.InnerIPAddress)
            logger.info('inner_port[%d]' % pConnectionInfoField.InnerPort)
            logger.info('outer_ip_address[%s]' % pConnectionInfoField.OuterIPAddress)
            logger.info('outer_port[%d]' % pConnectionInfoField.OuterPort)
            logger.info('mac_address[%s]' % pConnectionInfoField.MacAddress)

            # 请求登录
            login_req = traderapi.CTORATstpReqUserLoginField()
            login_req.LogInAccount = self.UserID
            login_req.LogInAccountType = traderapi.TORA_TSTP_LACT_UserID
            login_req.Password = self.Password
            login_req.UserProductInfo = 'DEMO'
            # login_req.TerminalInfo = 'PC;IIP=000.000.000.000;IPORT=00000;LIP=x.xx.xxx.xxx;MAC=123ABC456DEF;HD=XXXXXXXXXX'

            self.__req_id += 1
            ret = self.api.ReqUserLogin(login_req, self.__req_id)
            if ret != 0:
                logger.info('ReqUserLogin fail, ret[%d]' % ret)

        else:
            logger.error('GetConnectionInfo fail, [%d] [%d] [%s]!!!' % (
            nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def logout(self):
        # 登出
        if self.connect_status:
            req = traderapi.CTORATstpUserLogoutField()
            self.__req_id += 1
            ret = self.api.ReqUserLogout(req, self.__req_id)
            if ret != 0:
                logger.info('ReqUserLogout fail, ret[%d]' % ret)
            else:
                self.connect_status = False
    def _limitFrequency(self):
        delta = time.time() - self._last_query_time
        if delta < 0.5:
            time.sleep(0.5 - delta)
        self._last_query_time = time.time()

    def getInvester(self):
        # 查询投资者
        try:
            self._investor = []
            req_field = traderapi.CTORATstpQryInvestorField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryInvestor(req_field, self.__req_id))
            self.waitCompletion("查询投资者")
        except Exception as e:
            logger.error(e)
        return self._investor

    def getQuote(self):
        #查询股东账号
        try:
            self._share_account = []
            req_field = traderapi.CTORATstpQryShareholderAccountField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryShareholderAccount(req_field, self.__req_id))
            self.waitCompletion("查询股东账号")
        except Exception as e:
            logger.error(e)
        return self._share_account

    def getInstrument(self, code):
        # 查询合约
        try:
            self._instrument = []
            req_field = traderapi.CTORATstpQryInstrumentField()
            req_field.ExchangeID = traderapi.TORA_TSTP_EXD_SSE if code.startswith('SH') else traderapi.TORA_TSTP_EXD_SZSE
            req_field.SecurityID = code.replace('SH', '').replace('SZ', '')
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQrySecurity(req_field, self.__req_id))
            self.waitCompletion("查询合约")
        except Exception as e:
            logger.error(e)
        return self._instrument

    def getAccount(self):
        # 查询资金账号
        try:
            self._account = {}
            req_field = traderapi.CTORATstpQryTradingAccountField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryTradingAccount(req_field, self.__req_id))
            self.waitCompletion("获取资金账户")
        except Exception as e:
            logger.error(e)
        return [self.lastAccount, self.lastDataTime]

    def getOrders(self):
        # 查询报单
        try:
            self._orders = {}
            req_field = traderapi.CTORATstpQryOrderField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryOrder(req_field, self.__req_id))
            self.waitCompletion("查询报单")
        except Exception as e:
            logger.error(e)
        return [self.lastOrders, self.lastDataTime]

    
    def getTheOrder(self, sys_id):
        # 查询特定报单
        try:
            self._orders = {}
            req_field = traderapi.CTORATstpQryOrderField()
            req_field.OrderSysID = sys_id
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryOrder(req_field, self.__req_id))
            self.waitCompletion("查询特定报单")
        except Exception as e:
            logger.error(e)
        return self.lastOrders


    def getPositions(self):
        # 查询持仓
        try:
            self._positions = []
            req_field = traderapi.CTORATstpQryPositionField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryPosition(req_field, self.__req_id))
            self.waitCompletion("查询持仓")
        except Exception as e:
            logger.error(e)
        return [self.lastPositions, self.lastDataTime]

    def getTrades(self):
        # 查询成交
        try:
            self._trades = {}
            req_field = traderapi.CTORATstpQryTradeField()
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqQryTrade(req_field, self.__req_id))
            self.waitCompletion("查询成交")
        except Exception as e:
            logger.error(e)
        return [self.lastTrades, self.lastDataTime]

    def orderInsert(self, code, price, volume, order_type=traderapi.TORA_TSTP_OPT_LimitPrice):
        # 限价委托
        self._order_result = {}
        try:
            order_field = traderapi.CTORATstpInputOrderField()
            order_field.ExchangeID = traderapi.TORA_TSTP_EXD_SSE if code[:2] == "SH" else traderapi.TORA_TSTP_EXD_SZSE
            order_field.ShareholderID = self.SSE_ShareHolderID if code[:2] == "SH" else self.SZ_ShareHolderID
            order_field.SecurityID = code.replace("SH", "").replace("SZ", "")
            order_field.Direction = traderapi.TORA_TSTP_D_Buy if volume > 0 else traderapi.TORA_TSTP_D_Sell
            order_field.VolumeTotalOriginal = abs(volume)
            order_field.LimitPrice = price
            order_field.OrderPriceType = order_type
            order_field.TimeCondition = traderapi.TORA_TSTP_TC_GFD
            order_field.VolumeCondition = traderapi.TORA_TSTP_VC_AV
            logger.info(f"orderInsert {order_field.ExchangeID} {order_field.ShareholderID} {order_field.SecurityID} {order_field.Direction} {order_field.VolumeTotalOriginal} {order_field.LimitPrice} {order_field.OrderPriceType} {order_field.TimeCondition} {order_field.VolumeCondition}")
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqOrderInsert(order_field, self.__req_id))
            self.waitCompletion("限价委托")
        except Exception as e:
            logger.error(e)
        return self._order_result

    def deleteOrder(self, order_id, is_sse):
        # 撤单
        self._order_delete = {}
        try:
            order_field = traderapi.CTORATstpInputOrderActionField()
            order_field.OrderSysID = order_id
            order_field.ExchangeID = traderapi.TORA_TSTP_EXD_SSE if is_sse else traderapi.TORA_TSTP_EXD_SZSE
            order_field.ActionFlag = traderapi.TORA_TSTP_AF_Delete
            order_field.SInfo = 'python3.7'
            self.__req_id += 1
            self.resetCompletion()
            self._limitFrequency()
            self.checkApiReturn(self.api.ReqOrderAction(order_field, self.__req_id))
            self.waitCompletion("撤单")
        except Exception as e:
            logger.error(e)
        return self._order_delete


    def OnRspUserLogin(self, pRspUserLoginField: "traderapi.CTORATstpRspUserLoginField",
                       pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        try:
            if pRspInfoField.ErrorID == 0:
                logger.info('Login success! [%d]' % nRequestID)

                self.__front_id = pRspUserLoginField.FrontID
                self.__session_id = pRspUserLoginField.SessionID

            else:
                logger.info('Login fail!!! [%d] [%d] [%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
            return
        except Exception as e:
            logger.error(e)

    def OnRspUserPasswordUpdate(self, pUserPasswordUpdateField: "CTORATstpUserPasswordUpdateField",
                                pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        if pRspInfoField.ErrorID == 0:
            logger.info('OnRspUserPasswordUpdate: OK! [%d]' % nRequestID)
        else:
            logger.error('OnRspUserPasswordUpdate: Error! [%d] [%d] [%s]'
                  % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRspOrderInsert(self, pInputOrderField: "CTORATstpInputOrderField", pRspInfoField: "CTORATstpRspInfoField",
                         nRequestID: "int") -> "void":
        try:
            if pRspInfoField.ErrorID == 0:
                self._order_result = {
                    'UserRequestID': pInputOrderField.UserRequestID,
                    'ExchangeID': pInputOrderField.ExchangeID,
                    'InvestorID': pInputOrderField.InvestorID,
                    'BusinessUnitID': pInputOrderField.BusinessUnitID,
                    'ShareholderID': pInputOrderField.ShareholderID,
                    'SecurityID': pInputOrderField.SecurityID,
                    'Direction': pInputOrderField.Direction,
                    'LimitPrice': pInputOrderField.LimitPrice,
                    'VolumeTotalOriginal': pInputOrderField.VolumeTotalOriginal,
                    'OrderPriceType': pInputOrderField.OrderPriceType,
                    'TimeCondition': pInputOrderField.TimeCondition,
                    'VolumeCondition': pInputOrderField.VolumeCondition,
                    'Operway': pInputOrderField.Operway,
                    'OrderRef': pInputOrderField.OrderRef,
                    'LotType': pInputOrderField.LotType,
                    'OrderSysID': pInputOrderField.OrderSysID,
                    'CondCheck': pInputOrderField.CondCheck,
                    'GTDate': pInputOrderField.GTDate,
                    'ForceCloseReason': pInputOrderField.ForceCloseReason,
                    'CreditDebtID': pInputOrderField.CreditDebtID,
                    'CreditQuotaType': pInputOrderField.CreditQuotaType,
                    'DiscountCouponID': pInputOrderField.DiscountCouponID,
                    'SInfo': pInputOrderField.SInfo,
                }
                logger.info('OnRspOrderInsert: OK! [%d]' % nRequestID)
            else:
                logger.info('OnRspOrderInsert: Error! [%d] [%d] [%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
            self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspOrderAction(self, pInputOrderActionField: "CTORATstpInputOrderActionField",
                         pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        try:
            if pRspInfoField.ErrorID == 0:
                self._order_delete = {
                    'FrontID': pInputOrderActionField.FrontID,
                    'SessionID': pInputOrderActionField.SessionID,
                    'OrderRef': pInputOrderActionField.OrderRef,
                    'OrderSysID': pInputOrderActionField.OrderSysID,
                    'ActionFlag': pInputOrderActionField.ActionFlag,
                    'SInfo': pInputOrderActionField.SInfo
                }
                logger.info('OnRspOrderAction: OK! [%d]' % nRequestID)
            else:
                self._order_delete = {
                    'ErrorID': pRspInfoField.ErrorID,
                    'ErrorMsg': pRspInfoField.ErrorMsg
                }
                logger.info('OnRspOrderAction: Error! [%d] [%d] [%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
            self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspInquiryJZFund(self, pRspInquiryJZFundField: "CTORATstpRspInquiryJZFundField",
                           pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        if pRspInfoField.ErrorID == 0:
            logger.info('OnRspInquiryJZFund: OK! [%d] [%.2f] [%.2f]'
                  % (nRequestID, pRspInquiryJZFundField.UsefulMoney, pRspInquiryJZFundField.FetchLimit))
        else:
            logger.error('OnRspInquiryJZFund: Error! [%d] [%d] [%s]'
                  % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRspTransferFund(self, pInputTransferFundField: "CTORATstpInputTransferFundField",
                          pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int") -> "void":
        if pRspInfoField.ErrorID == 0:
            logger.info('OnRspTransferFund: OK! [%d]' % nRequestID)
        else:
            logger.error('OnRspTransferFund: Error! [%d] [%d] [%s]'
                  % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))

    def OnRtnOrder(self, pOrderField: "CTORATstpOrderField") -> "void":
        try:
            print("OnRtnOrder")
            print(
                'OnRtnOrder: InvestorID[%s] SecurityID[%s] OrderRef[%d] OrderLocalID[%s] LimitPrice[%.2f] VolumeTotalOriginal[%d] OrderSysID[%s] OrderStatus[%s]'
                % (pOrderField.InvestorID, pOrderField.SecurityID, pOrderField.OrderRef, pOrderField.OrderLocalID,
                   pOrderField.LimitPrice, pOrderField.VolumeTotalOriginal, pOrderField.OrderSysID,
                   pOrderField.OrderStatus))
        except Exception as e:
            print(e)

    def OnRtnTrade(self, pTradeField: "CTORATstpTradeField") -> "void":
        try:
            print("OnRtnTrade")
            print(
                'OnRtnTrade: TradeID[%s] InvestorID[%s] SecurityID[%s] OrderRef[%d] OrderLocalID[%s] Price[%.2f] Volume[%d]'
                % (pTradeField.TradeID, pTradeField.InvestorID, pTradeField.SecurityID,
                   pTradeField.OrderRef, pTradeField.OrderLocalID, pTradeField.Price, pTradeField.Volume))
        except Exception as e:
            print(e)

    def OnRtnMarketStatus(self, pMarketStatusField: "CTORATstpMarketStatusField") -> "void":
        logger.info('OnRtnMarketStatus: MarketID[%s] MarketStatus[%s]'
              % (pMarketStatusField.MarketID, pMarketStatusField.MarketStatus))

    def OnRspQrySecurity(self, pSecurityField: "CTORATstpSecurityField", pRspInfoField: "CTORATstpRspInfoField",
                         nRequestID: "int", bIsLast: "bool") -> "void":
        logger.info(F"OnRspQrySecurity")
        try:
            if bIsLast != 1:
                logger.info(
                    'OnRspQrySecurity[%d]: SecurityID[%s] SecurityName[%s] MarketID[%s] OrderUnit[%s] OpenDate[%s] UpperLimitPrice[%.2f] LowerLimitPrice[%.2f]'
                    % (nRequestID, pSecurityField.SecurityID, pSecurityField.SecurityName, pSecurityField.MarketID,
                       pSecurityField.OrderUnit, pSecurityField.OpenDate, pSecurityField.UpperLimitPrice,
                       pSecurityField.LowerLimitPrice))
            else:
                logger.info('查询合约结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
        except Exception as e:
            logger.error(e)

    def OnRspQryInvestor(self, pInvestorField: "CTORATstpInvestorField", pRspInfoField: "CTORATstpRspInfoField",
                         nRequestID: "int", bIsLast: "bool") -> "void":
        if bIsLast != 1:
            self._investor.append({"InvestorID": pInvestorField.InvestorID,
                                   "Operways": pInvestorField.Operways})
            logger.info('OnRspQryInvestor[%d]: InvestorID[%s]  Operways[%s]'
                  % (nRequestID, pInvestorField.InvestorID,
                     pInvestorField.Operways))
        else:
            logger.error('查询投资者结束[%d] ErrorID[%d] ErrorMsg[%s]'
                  % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
            self.notifyCompletion()

    def OnRspQryShareholderAccount(self, pShareholderAccountField: "CTORATstpShareholderAccountField",
                                   pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int",
                                   bIsLast: "bool") -> "void":
        logger.info("OnRspQryShareholderAccount")
        try:
            if bIsLast != 1:
                self._share_account.append({"InvestorID": pShareholderAccountField.InvestorID,
                                            "ExchangeID": pShareholderAccountField.ExchangeID,
                                            "ShareholderID": pShareholderAccountField.ShareholderID})
                logger.info('OnRspQryShareholderAccount[%d]: InvestorID[%s] ExchangeID[%s] ShareholderID[%s]'
                      % (nRequestID, pShareholderAccountField.InvestorID, pShareholderAccountField.ExchangeID,
                         pShareholderAccountField.ShareholderID))
            else:
                logger.info('查询股东账户结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
                self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspQryTradingAccount(self, pTradingAccountField: "CTORATstpTradingAccountField",
                               pRspInfoField: "CTORATstpRspInfoField", nRequestID: "int", bIsLast: "bool") -> "void":
        try:
            if bIsLast != 1:
                for attr_name in dir(pTradingAccountField):
                    if not attr_name.startswith("__"):
                        attr_value = getattr(pTradingAccountField, attr_name)
                        if type(attr_value) == float:
                            setattr(pTradingAccountField, attr_name, round(attr_value, 2))
                self._account[pTradingAccountField.AccountID] = {
                    "PreDeposit": round(pTradingAccountField.PreDeposit, 2),
                    "FetchLimit": round(pTradingAccountField.FetchLimit, 2),
                    "UsefulMoney": round(pTradingAccountField.UsefulMoney, 2),
                    "FrozenCash": round(pTradingAccountField.FrozenCash, 2),
                }
                logger.info(
                    'OnRspQryTradingAccount[%d]: DepartmentID[%s] InvestorID[%s] AccountID[%s] CurrencyID[%s] UsefulMoney[%.2f] FetchLimit[%.2f]'
                    % (nRequestID, pTradingAccountField.DepartmentID, pTradingAccountField.InvestorID,
                       pTradingAccountField.AccountID, pTradingAccountField.CurrencyID,
                       pTradingAccountField.UsefulMoney, pTradingAccountField.FetchLimit))
            else:
                logger.info('查询资金账号结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
                self.lastAccount = self._account
                self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspQryOrder(self, pOrderField: "CTORATstpOrderField", pRspInfoField: "CTORATstpRspInfoField",
                      nRequestID: "int", bIsLast: "bool") -> "void":
        try:
            logger.info("OnRspQryOrder {}".format(bIsLast))
            if bIsLast != 1:
                for attr_name in dir(pOrderField):
                    if not attr_name.startswith("__"):
                        attr_value = getattr(pOrderField, attr_name)
                        if type(attr_value) == float:
                            setattr(pOrderField, attr_name, round(attr_value, 2))
                self._orders[pOrderField.OrderLocalID] = {
                    "ExchangeID": pOrderField.ExchangeID,
                    "SecurityID": pOrderField.SecurityID,
                    "OrderLocalID": pOrderField.OrderLocalID,
                    "OrderRef": pOrderField.OrderRef,
                    "OrderSysID": pOrderField.OrderSysID,
                    "VolumeTotalOriginal": pOrderField.VolumeTotalOriginal,
                    "VolumeTraded": pOrderField.VolumeTraded,
                    "OrderStatus": pOrderField.OrderStatus,
                    "OrderSubmitStatus": pOrderField.OrderSubmitStatus,
                    "StatusMsg": pOrderField.StatusMsg,
                    "LimitPrice": pOrderField.LimitPrice,
                    "OrderPriceType": pOrderField.OrderPriceType,
                    "Direction": pOrderField.Direction,
                    "InsertDate": pOrderField.InsertDate,
                    "InsertTime": pOrderField.InsertTime
                }
                print(
                    'OnRspQryOrder[%d]: SecurityID[%s] OrderLocalID[%s] OrderRef[%d] OrderSysID[%s] VolumeTotalOriginal[%d] VolumeTraded[%d] OrderStatus[%s] OrderSubmitStatus[%s], StatusMsg[%s]'
                    % (nRequestID, pOrderField.SecurityID, pOrderField.OrderLocalID, pOrderField.OrderRef,
                       pOrderField.OrderSysID, pOrderField.VolumeTotalOriginal, pOrderField.VolumeTraded,
                       pOrderField.OrderStatus, pOrderField.OrderSubmitStatus, pOrderField.StatusMsg))
            else:
                logger.info('查询报单结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
                self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
                self.lastOrders = self._orders
                self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspQryPosition(self, pPositionField: "CTORATstpPositionField", pRspInfoField: "CTORATstpRspInfoField",
                         nRequestID: "int", bIsLast: "bool") -> "void":
        logger.info("OnRspQryPosition {}".format(bIsLast))
        try:
            if bIsLast != 1:
                for attr_name in dir(pPositionField):
                    if not attr_name.startswith("__"):
                        attr_value = getattr(pPositionField, attr_name)
                        if type(attr_value) == float:
                            setattr(pPositionField, attr_name, round(attr_value, 2))
                print('OnRspQryPosition[%d]: InvestorID[%s] SecurityID[%s] HistoryPos[%d] TodayBSPos[%d] TodayPRPos[%d]'
                      % (nRequestID, pPositionField.InvestorID, pPositionField.SecurityID, pPositionField.HistoryPos,
                         pPositionField.TodayBSPos, pPositionField.TodayPRPos))
                self._positions.append(
                    {
                        "ExchangeID": pPositionField.ExchangeID,
                        "InvestorID": pPositionField.InvestorID,
                        "BusinessUnitID": pPositionField.BusinessUnitID,
                        "MarketID": pPositionField.MarketID,
                        "ShareholderID": pPositionField.ShareholderID,
                        "TradingDay": pPositionField.TradingDay,
                        "SecurityID": pPositionField.SecurityID,
                        "SecurityName": pPositionField.SecurityName,
                        "HistoryPos": pPositionField.HistoryPos,
                        "HistoryPosFrozen": pPositionField.HistoryPosFrozen,
                        "TodayBSPos": pPositionField.TodayBSPos,
                        "TodayBSPosFrozen": pPositionField.TodayBSPosFrozen,
                        "TodayPRPos": pPositionField.TodayPRPos,
                        "TodayPRPosFrozen": pPositionField.TodayPRPosFrozen,
                        "TodaySMPos": pPositionField.TodaySMPos,
                        "TodaySMPosFrozen": pPositionField.TodaySMPosFrozen,
                        "HistoryPosPrice": pPositionField.HistoryPosPrice,
                        "TotalPosCost": round(pPositionField.TotalPosCost, 2),
                        "PrePosition": pPositionField.PrePosition,
                        "AvailablePosition": pPositionField.AvailablePosition,
                        "CurrentPosition": pPositionField.CurrentPosition,
                        "OpenPosCost": pPositionField.OpenPosCost,
                        "CreditBuyPos": pPositionField.CreditBuyPos,
                        "CreditSellPos": pPositionField.CreditSellPos,
                        "TodayCreditSellPos": pPositionField.TodayCreditSellPos,
                        "CollateralOutPos": pPositionField.CollateralOutPos,
                        "RepayUntradeVolume": pPositionField.RepayUntradeVolume,
                        "RepayTransferUntradeVolume": pPositionField.RepayTransferUntradeVolume,
                        "CollateralBuyUntradeAmount": pPositionField.CollateralBuyUntradeAmount,
                        "CollateralBuyUntradeVolume": pPositionField.CollateralBuyUntradeVolume,
                        "CreditBuyAmount": pPositionField.CreditBuyAmount,
                        "CreditBuyUntradeAmount": pPositionField.CreditBuyUntradeAmount,
                        "CreditBuyFrozenMargin": pPositionField.CreditBuyFrozenMargin,
                        "CreditBuyInterestFee": pPositionField.CreditBuyInterestFee,
                        "CreditBuyUntradeVolume": pPositionField.CreditBuyUntradeVolume,
                        "CreditSellAmount": pPositionField.CreditSellAmount,
                        "CreditSellUntradeAmount": pPositionField.CreditSellUntradeAmount,
                        "CreditSellFrozenMargin": pPositionField.CreditSellFrozenMargin,
                        "CreditSellInterestFee": pPositionField.CreditSellInterestFee,
                        "CreditSellUntradeVolume": pPositionField.CreditSellUntradeVolume,
                        "CollateralInPos": pPositionField.CollateralInPos,
                        "CreditBuyFrozenCirculateMargin": pPositionField.CreditBuyFrozenCirculateMargin,
                        "CreditSellFrozenCirculateMargin": pPositionField.CreditSellFrozenCirculateMargin,
                        "CloseProfit": pPositionField.CloseProfit,
                        "TodayTotalOpenVolume": pPositionField.TodayTotalOpenVolume,
                        "TodayCommission": pPositionField.TodayCommission,
                        "TodayTotalBuyAmount": pPositionField.TodayTotalBuyAmount,
                        "TodayTotalSellAmount": pPositionField.TodayTotalSellAmount,
                    }
                )
            else:
                logger.info('查询持仓结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
                self.lastPositions = self._positions
                self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
                self.notifyCompletion()
        except Exception as e:
            logger.error(e)

    def OnRspQryTrade(self, pTradeField: "CTORATstpTradeField", pRspInfoField: "CTORATstpRspInfoField",
                         nRequestID: "int", bIsLast: "bool") -> "void":
        try:
            if bIsLast != 1:
                for attr_name in dir(pTradeField):
                    if not attr_name.startswith("__"):
                        attr_value = getattr(pTradeField, attr_name)
                        if type(attr_value) == float:
                            setattr(pTradeField, attr_name, round(attr_value, 2))
                self._trades[pTradeField.TradeID] = {
                    "ExchangeID": pTradeField.ExchangeID,
                    "InvestorID": pTradeField.InvestorID,
                    "BusinessUnitID": pTradeField.BusinessUnitID,
                    "SecurityID": pTradeField.SecurityID,
                    "ShareholderID": pTradeField.ShareholderID,
                    "TradeID": pTradeField.TradeID,
                    "TradeTime": pTradeField.TradeTime,
                    "Direction": pTradeField.Direction,
                    "OrderSysID": pTradeField.OrderSysID,
                    "OrderLocalID": pTradeField.OrderLocalID,
                    "Price": pTradeField.Price,
                    "Volume": pTradeField.Volume,
                    "TradeDate": pTradeField.TradeDate,
                    "TradingDay": pTradeField.TradingDay,
                    "OrderRef": pTradeField.OrderRef,
                    "AccountID": pTradeField.AccountID
                }
            else:
                
                logger.info('查询成交结束[%d] ErrorID[%d] ErrorMsg[%s]'
                      % (nRequestID, pRspInfoField.ErrorID, pRspInfoField.ErrorMsg))
                self.lastDataTime = datetime.datetime.now(timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
                self.lastTrades = self._trades
                self.notifyCompletion()
        except Exception as e:
            logger.error(e)
