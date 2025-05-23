import React from 'react';

function OutputPanel({ analyticsResult }) {
  if (!analyticsResult) {
    return (
      <div className="card right">
        <h2>Analytics Results</h2>
        <p>Waiting for data...</p>
      </div>
    );
  }

  // Check for error in analytics result
  if (analyticsResult.error) {
    return (
      <div className="card right">
        <h2>Analytics Results</h2>
        <div className="error-message">
          Error: {analyticsResult.error}
        </div>
      </div>
    );
  }

  const formatCurrency = (val) => `$${val.toFixed(6)}`;
  const formatBps = (bps) => `${bps.toFixed(6)} bps (${(bps / 10000).toFixed(7)}%)`;

  return (
    <div className="card right">
      <h2>Analytics Results</h2>
      <p><strong>Expected Slippage:</strong> {formatBps(analyticsResult.slippage.bps)} — {formatCurrency(analyticsResult.slippage.cost)}</p>
      <p><strong>Expected Fees:</strong> {formatCurrency(analyticsResult.fees.amount)} ({(analyticsResult.fees.weighted_rate * 100).toFixed(2)}%)</p>
      <p><strong>Expected Market Impact:</strong> {formatBps(analyticsResult.market_impact.total_bps)} — {formatCurrency(analyticsResult.market_impact.cost)}</p>
      <p><strong>Net Cost:</strong> {formatBps(analyticsResult.net_cost.bps)} — {formatCurrency(analyticsResult.net_cost.amount)}</p>
      <p><strong>Maker/Taker Proportion:</strong> {(analyticsResult.maker_taker.maker_ratio * 100).toFixed(1)}% / {(analyticsResult.maker_taker.taker_ratio * 100).toFixed(1)}%</p>
      <p><strong>Internal Latency:</strong> {analyticsResult.latency.processing_time_ms.toFixed(2)} ms</p>
      <p className="timestamp">Last updated: {new Date().toLocaleTimeString()}</p>
    </div>
  );
}

export default OutputPanel;
