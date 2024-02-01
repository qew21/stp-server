# 奇点股票STP接口Python Web服务

轻量级Python Web服务封装，单页React前端，可查询证券账户及下单交易，支持仿真和实盘。

对接了L1和L2行情服务，L2需要在特定环境使用。

#### 模拟账户注册方式：

https://n-sight.com.cn/

#### 接口版本：

API_Python3.7_行情_v1.0.5_20230210  
API_Python3.7_交易_v4.0.6_20230130  

#### 仿真测试环境：

行情前置地址：tcp://210.14.72.21:4402  
交易前置地址：tcp://210.14.72.21:4400  
#可用时段：同交易所交易时间，价格同步交易所，一般延迟3秒，开盘延迟可能略长一点。成交数量则包含其他仿真参与者撮合成交量。  
注：正常情况下，仿真柜台在交易日早上9:25后可登录，模拟环境无集合竞价行情  


## 演示效果
![效果图](https://github.com/qew21/stp-server/blob/master/demo.gif)
## 使用

### 配置server/account.yaml

配置STP实盘账号或仿真账号
```yaml
    md_server: tcp://210.14.72.21:4402
    trader_server: tcp://210.14.72.21:4400
    InvestorID: "*****"
    UserID: "*****"
    AccountID: "*****"
    Password: "*****"
    DepartmentID: "*****"
    SSE_ShareHolderID: '*****'
    SZ_ShareHolderID: '*****'
```

### 启动服务
- SDK限定使用Python3.7
```bash
python3.7 -m venv venv
pip install --upgrade pip setuptools -i https://mirrors.aliyun.com/pypi/simple
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
cd server
export PYTHONPATH=.
python app/stp_service.py
```

### 启动展示页面

```shell
npm install && npm start  
```





