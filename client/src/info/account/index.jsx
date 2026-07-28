import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table } from 'antd';

const AccountTable = ({ totalMarketValue }) => {
    const { refreshToken } = useRefresh();

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [accounts, setAccounts] = useState([]);

    useEffect(() => {
        const fetchAccounts = async () => {
            api.get('/get_account')
                .then(res => {
                    const accountData = res.data[0];
                    const transformedData = Object.keys(accountData).map(key => ({
                        accountName: key,
                        marketValue: totalMarketValue,
                        TotalAssets: accountData[key].UsefulMoney + totalMarketValue,  // 假设 TotalAssets 是账户总额
                        ...accountData[key]
                    }));
                    setAccounts(transformedData);
                })
                .catch(error => {
                    console.error(error);
                });

        };

        fetchAccounts();
    }, [refreshToken, totalMarketValue]);

    const columns = [
        {
            title: '账户名称',
            dataIndex: 'accountName',
            key: 'accountName',
        },
        {
            title: '账户总额',
            dataIndex: 'TotalAssets',
        },
        {
            title: '持仓市值',
            dataIndex: 'marketValue',
        },
        {
            title: '上日结存',
            dataIndex: 'PreDeposit',
        },
        {
            title: '可用资金',
            dataIndex: 'UsefulMoney',
        },
        {
            title: '冻结资金',
            dataIndex: 'FrozenCash',
        },
    ];

    return (
        <div>
            {accounts.map((account, index) => (
                <Table 
                    key={index}
                    columns={columns} 
                    dataSource={[account]} 
                    onChange={onChange} 
                    pagination={false} 
                />
            ))}
        </div>
    );
}
export default AccountTable;