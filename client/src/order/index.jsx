import React, { useState } from 'react';
import { Radio, Select, InputNumber, Button, message, Input } from 'antd';
import api from '../utils/Request';
import { useRefresh } from '../utils/Context';



const OrderForm = () => {
    const { triggerRefresh } = useRefresh();
    const [name, setName] = useState('');
    const [direction, setDirection] = useState(1);
    const [priceType, setPriceType] = useState('market');
    const [price, setPrice] = useState('');
    const [volume, setVolume] = useState(100);
    

    const handleSubmit = async () => {
        try {
            if (priceType === 'market') {
                api.get(`/order_market?code=${name}&volume=${volume * direction}`)
                    .then(res => {
                        message.success(`下单成功 ${JSON.stringify(res.data, null, 2)}`);
                        triggerRefresh();
                    })
                    .catch(error => {
                        message.success(`下单失败 ${error}`);
                    });
            } else {
                api.get(`/order_limit?code=${name}&volume=${volume * direction}&price=${price}`)
                    .then(res => {
                        message.success(`下单成功 ${JSON.stringify(res.data, null, 2)}`);
                        triggerRefresh();
                    })
                    .catch(error => {
                        message.success(`下单失败 ${error}`);
                    });
            }
            console.log(name, direction, priceType, price, volume);
        } catch (error) {
            message.error(`下单失败 ${error}`);
        }
    };

    return (
        
        <div style={{ padding: 20 }}>
            <Input
                style={{ width: 200, marginBottom: 16, marginRight: 8 }}
                placeholder="股票代码，SH或SZ开头"
                value={name}
                onChange={e => setName(e.target.value)}
            />
            <Radio.Group onChange={e => setDirection(e.target.value)} value={direction} style={{ marginBottom: 16 }}>
                <Radio value={1}>买入</Radio>
                <Radio value={-1}>卖出</Radio>
            </Radio.Group>
            <Select defaultValue="market" style={{ width: 80, marginRight: 8, marginBottom: 16 }} onChange={setPriceType} >
                <Select.Option value="market">市价</Select.Option>
                <Select.Option value="limit">限价</Select.Option>
            </Select>
            {priceType === 'limit' && (
                <InputNumber
                    style={{ width: 200, marginRight: 8, marginBottom: 16 }}
                    addonBefore="价格"
                    value={price}
                    min={0}
                    step={0.02}
                    onChange={value => setPrice(value)}
                />
            )}
            数目
            <InputNumber
                style={{ width: 80, marginLeft: 8, marginRight: 8, marginBottom: 16 }}
                min={100}
                value={volume}
                step={100}
                onChange={value => setVolume(value)}
            />
            <Button type="primary" onClick={handleSubmit} style={{ marginBottom: 16 }}>
                确认
            </Button>
        </div>
        
    );
};

export default OrderForm;
