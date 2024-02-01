import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table, Button } from 'antd';

const OrdersTable = () => {
    const { refreshToken } = useRefresh();

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [orders, setOrders] = useState([]);
    const exchange = {"1": "SH", "2": "SZ"};
    const direction_dict = {"0": "买入", "1": "卖出"};
    const order_status = {
        "0": "预埋",
        "1": "未知",
        "2": "交易所已接收",
        "3": "部分成交",
        "4": "全部成交",
        "5": "部成部撤",
        "6": "全部撤单",
        "7": "交易所已拒绝",
        "8": "发往交易核心"
    };
    const price_type_dict = {
        1: "任意价",
        2: "限价",
        3: "最优价",
        4: "盘后定价",
        5: "五档价",
        6: "本方最优",
    };

    const fetchOrders = async () => {
        api.get('/get_orders')
            .then(res => {
                const transformedData = Object.entries(res.data[0])
                .filter(([key, item]) => item.OrderStatus !== '6')
                .map(([key, item]) => ({
                    'order_id': key,
                    code: exchange[item.ExchangeID] + item.SecurityID,
                    price_type: price_type_dict[item.OrderPriceType],
                    insert_time: item.InsertDate + ' ' + item.InsertTime,  
                    status: order_status[item.OrderStatus],  
                    direction: direction_dict[item.Direction],
                    ...item
                }));
                console.log(transformedData);
                setOrders(transformedData);
            })
            .catch(error => {
                console.error(error);
            });
    };

    useEffect(() => {
        fetchOrders();
    }, [refreshToken]);

    const handleCancelOrder = async (orderId) => {
        try {
            api.get(`/order_delete?order_id=${orderId}`)
                .then(res => {
                    console.log(res.data);
                    fetchOrders();
                })
                .catch(error => {
                    console.error(error);
                });
        } catch (error) {
            console.error(error);
        }
    };

    const columns = [
        {
            title: '挂单单号',
            dataIndex: 'order_id',
            sorter: (a, b) => a.order_id.localeCompare(b.order_id),
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
            title: '数目',
            dataIndex: 'VolumeTotalOriginal',
            sorter: (a, b) => a.VolumeTotalOriginal - b.VolumeTotalOriginal,
        },
        {
            title: '价格',
            dataIndex: 'LimitPrice',
            sorter: (a, b) => a.LimitPrice - b.LimitPrice,
        },
        {
            title: '类型',
            dataIndex: 'price_type',
            sorter: (a, b) => a.price_type.localeCompare(b.price_type),
        },
        {
            title: '下单时间',
            dataIndex: 'insert_time',
            sorter: (a, b) => a.insert_time.localeCompare(b.insert_time),
        },
        {
            title: '成交量',
            dataIndex: 'VolumeTraded',
            sorter: (a, b) => a.VolumeTraded - b.VolumeTraded,
        },
        {
            title: '状态',
            dataIndex: 'status',
            sorter: (a, b) => a.status.localeCompare(b.status),
        },
    ];

    return <Table columns={columns} dataSource={orders} onChange={onChange} pagination={orders.length > 10} />;
}
export default OrdersTable;