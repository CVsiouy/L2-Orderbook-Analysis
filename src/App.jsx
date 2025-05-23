import React, { useState, useEffect } from 'react';
import './App.css';
import './styles.css'
import InputPanel from './components/InputPanel';
import OutputPanel from './components/OutputPanel';
import OrderbookStatus from './components/OrderbookStatus';
import { io } from 'socket.io-client';

function App() {
  const [params, setParams] = useState({
    exchange: 'OKX',
    symbol: 'BTC-USDT-SWAP',
    order_type: 'market',
    quantity: 100,
    volatility: 0.3,
    fee_tier: 'VIP0',
  });

  const [orderbook, setOrderbook] = useState(null);
  const [analyticsResult, setAnalyticsResult] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [socket, setSocket] = useState(null);

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io('import.meta.env.VITE_SOCKET_URL');
    setSocket(newSocket);

    // Clean up on unmount
    return () => {
      if (newSocket) newSocket.disconnect();
    };
  }, []);

  // Set up socket event listeners
  useEffect(() => {
    if (!socket) return;

    // Connection events
    socket.on('connect', () => {
      console.log('Connected to websocket server');
      setConnected(true);
      setError(null);
    });

    socket.on('disconnect', () => {
      console.warn('WebSocket disconnected');
      setConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('Websocket connection error:', err);
      setError('WebSocket connection failed');
      setConnected(false);
    });

    // Data events
    socket.on('orderbook_update', (data) => {
      setOrderbook(data);
    });

    socket.on('analytics_update', (data) => {
      setAnalyticsResult(data);
    });

    socket.on('connection_status', (status) => {
      setConnected(status.connected);
    });

    socket.on('error', (errorData) => {
      console.error('Error from server:', errorData);
      setError(errorData.message);
    });

    socket.on('parameter_update', (updatedParams) => {
      setParams(updatedParams);
    });

  }, [socket]);

  // Handle parameter changes
  const handleParamChange = (e) => {
    const { name, value } = e.target;
    
    // Update local state
    setParams((prev) => ({
      ...prev,
      [name]: ['quantity', 'volatility'].includes(name)
        ? parseFloat(value)
        : value,
    }));
    
    // Send parameter update to server
    if (socket && socket.connected) {
      socket.emit('parameter_update', { [name]: value });
    }
  };

  return (
    <div className="container">
      <h1>High-Performance Trade Simulator</h1>

      <OrderbookStatus connected={connected} orderbook={orderbook} error={error} />

      <div className="grid">
        <InputPanel
          params={params}
          onChange={handleParamChange}
          connected={connected}
        />

        <OutputPanel analyticsResult={analyticsResult} />
      </div>
    </div>
  );
}

export default App;
