import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table } from 'antd';

const TradesTable = () => {
    const { refreshToken } = useRefresh();
    
    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [trades, setTrades] = useState([]);
    const exchange = {"1": "SH", "2": "SZ"};
    const direction_dict = {"0": "买入", "1": "卖出"};

    useEffect(() => {
        const fetchTrades = async () => {
            api.get('/get_trades')
                .then(res => {
                    const tradesList = Object.entries(res.data[0]).map(([key, item]) => ({
                        'trade_id': key,
                        code: exchange[item.ExchangeID] + item.SecurityID,
                        insert_time: item.TradeDate + ' ' + item.TradeTime,  
                        direction: direction_dict[item.Direction],
                        ...item
                    }));
                    setTrades(tradesList);
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchTrades();
    }, [refreshToken]);

    const columns = [
        {
            title: '成交单号',
            dataIndex: 'trade_id',
            sorter: (a, b) => a.trade_id.localeCompare(b.trade_id),
        },
        {
            title: '证券代码',
            dataIndex: 'code',
            sorter: (a, b) => a.code.localeCompare(b.code),
        },
        {
            title: '方向',
            dataIndex: 'direction',
            sorter: (a, b) => a.direction.localeCompare(b.direction),
        },
        {
            title: '挂单单号',
            dataIndex: 'OrderLocalID',
            sorter: (a, b) => a.OrderLocalID.localeCompare(b.OrderLocalID),
        },
        {
            title: '数目',
            dataIndex: 'Volume',
            sorter: (a, b) => a.Volume - b.Volume,
        },
        {
            title: '价格',
            dataIndex: 'Price',
            sorter: (a, b) => a.Price - b.Price,
        },
        {
            title: '成交时间',
            dataIndex: 'insert_time',
            sorter: (a, b) => a.insert_time.localeCompare(b.insert_time),
        }
    ];

    return <Table columns={columns} dataSource={trades} onChange={onChange} pagination={trades.length > 10}/>;
}
export default TradesTable;