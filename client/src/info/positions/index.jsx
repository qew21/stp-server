import React, { useState, useEffect } from 'react';
import api from '../../utils/Request';
import { useRefresh } from '../../utils/Context';
import { Table, Input } from 'antd';


const SearchInput = ({ onSearch }) => {
    return <Input placeholder="搜索" onChange={e => onSearch(e.target.value)} />;
};


const PositionsTable = ({ onTotalValueChange }) => {
    const { refreshToken } = useRefresh();

    

    const onChange = (pagination, filters, sorter, extra) => {
        console.log('params', pagination, filters, sorter, extra);
    };

    const [positions, setPositions] = useState([]);
    const [filteredPositions, setFilteredPositions] = useState([]);
    const exchange = {"1": "SH", "2": "SZ"}


    const handleSearch = (value, dataIndex) => {
        const filteredData = positions.filter(item => {
            const itemData = item[dataIndex].toString();
            const searchText = value.toLowerCase();
            return itemData.includes(searchText);
        });
        setFilteredPositions(filteredData);
    };


    useEffect(() => {
        const fetchPositions = async () => {
            api.get('/get_position')
                .then(res => {
                    const transformedData = res.data[0].map(item => ({
                        code: exchange[item.MarketID] + item.SecurityID,
                        SecurityName: item.SecurityName,
                        CurrentPosition: item.CurrentPosition,
                        open: item.CurrentPosition >  0 ? (item.TotalPosCost / item.CurrentPosition).toFixed(2) : 0,
                        cost: item.TotalPosCost,
                        profit: item.CloseProfit,
                        today_position: item.TodayTotalOpenVolume, 
                        ...item
                    }));
                    setPositions(transformedData);
                    setFilteredPositions(transformedData)
                    // 计算市值总和
                    const totalValue = transformedData.reduce((acc, item) => acc + item.value, 0);
                    onTotalValueChange(totalValue); // 传递总市值到父组件
                })
                .catch(error => {
                    console.error(error);
                });
        };

        fetchPositions();
    }, [refreshToken, onTotalValueChange]);

    const columns = [
        {
            title: '证券代码',
            dataIndex: 'code',
            sorter: (a, b) => a.code.localeCompare(b.code),
            filterDropdown: ({ setSelectedKeys, confirm, clearFilters }) => (
                <div style={{ padding: 8 }}>
                    <SearchInput onSearch={value => handleSearch(value, 'code')} />
                </div>
            ),
        },
        {
            title: '证券名称',
            dataIndex: 'SecurityName',
            sorter: (a, b) => a.SecurityName.localeCompare(b.SecurityName),
            filterDropdown: ({ setSelectedKeys, confirm, clearFilters }) => (
                <div style={{ padding: 8 }}>
                    <SearchInput onSearch={value => handleSearch(value, 'SecurityName')} />
                </div>
            ),
        },
        {
            title: '当前持仓',
            dataIndex: 'CurrentPosition',
            sorter: (a, b) => a.CurrentPosition - b.CurrentPosition,
        },
        {
            title: '开仓价',
            dataIndex: 'open',
            sorter: (a, b) => a.open - b.open,
        },
        {
            title: '持仓成本',
            dataIndex: 'cost',
            sorter: (a, b) => a.cost - b.cost,
        },
        {
            title: '最新价',
            dataIndex: 'latest',
            sorter: (a, b) => a.latest - b.latest,
        },
        {
            title: '市值',
            dataIndex: 'value',
            sorter: (a, b) => a.value - b.value,
        },
        {
            title: '持仓盈亏',
            dataIndex: 'profit',
            sorter: (a, b) => a.profit - b.profit,
        },
        {
            title: '今日持仓',
            dataIndex: 'today_position',
            sorter: (a, b) => a.today_position - b.today_position,
        },
    ];

    return <Table columns={columns} dataSource={filteredPositions} onChange={onChange} pagination={positions.length > 10} />;
}
export default PositionsTable;