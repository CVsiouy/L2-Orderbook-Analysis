import React from 'react';

function OrderbookStatus({ connected, orderbook, error }) {
  const getStatusClass = () => {
    if (error) return 'status-error';
    if (connected) return 'status-connected';
    return 'status-disconnected';
  };

  const getStatusText = () => {
    if (error) return `Error: ${error}`;
    if (connected) {
      if (orderbook) {
        return `Connected - Last update: ${new Date().toLocaleTimeString()}`;
      }
      return 'Connected - Waiting for data...';
    }
    return 'Disconnected from server';
  };

  const getOrderbookInfo = () => {
    if (!orderbook || !connected) return null;
    
    const askCount = orderbook.asks ? orderbook.asks.length : 0;
    const bidCount = orderbook.bids ? orderbook.bids.length : 0;
    
    return (
      <span className="orderbook-info">
        {orderbook.symbol} - {askCount} asks, {bidCount} bids
      </span>
    );
  };

  return (
    <div className={`status-bar ${getStatusClass()}`}>
      <div className="status-indicator"></div>
      <div className="status-text">{getStatusText()}</div>
      {getOrderbookInfo()}
    </div>
  );
}

export default OrderbookStatus;
