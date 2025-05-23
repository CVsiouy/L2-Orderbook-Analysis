import React from 'react';

function InputPanel({ params, onChange, connected }) {
  return (
    <div className="card left">
      <h2>Input Parameters</h2>

      <label>Exchange</label>
      <select 
        name="exchange" 
        value={params.exchange} 
        onChange={onChange}
        disabled={!connected}
      >
        <option value="OKX">OKX</option>
      </select>

      <label>Symbol</label>
      <select 
        name="symbol" 
        value={params.symbol} 
        onChange={onChange}
        disabled={!connected}
      >
        <option value="BTC-USDT-SWAP">BTC-USDT-SWAP</option>
      </select>

      <label>Order Type</label>
      <select 
        name="order_type" 
        value={params.order_type} 
        onChange={onChange}
        disabled={!connected}
      >
        <option value="market">market</option>
        <option value="limit">limit</option>
      </select>

      <label>Quantity (USD)</label>
      <input
        type="number"
        name="quantity"
        value={params.quantity}
        onChange={onChange}
        min="1"
        step="1"
        disabled={!connected}
      />

      <label>Volatility</label>
      <input
        type="number"
        name="volatility"
        step="0.01"
        min="0.01"
        max="2"
        value={params.volatility}
        onChange={onChange}
        disabled={!connected}
      />

      <label>Fee Tier</label>
      <select 
        name="fee_tier" 
        value={params.fee_tier} 
        onChange={onChange}
        disabled={!connected}
      >
        <option value="VIP0">VIP0</option>
        <option value="VIP1">VIP1</option>
        <option value="VIP2">VIP2</option>
        <option value="VIP3">VIP3</option>
        <option value="VIP4">VIP4</option>
        <option value="VIP5">VIP5</option>
      </select>

      {!connected && (
        <div className="error-message">
          Disconnected from server. Parameters cannot be changed.
        </div>
      )}
    </div>
  );
}

export default InputPanel;
