import numpy as np
from sklearn.linear_model import LinearRegression
import time

class SlippageEstimator:
    def __init__(self):
        self.model = LinearRegression()
        self.historical_data = []  # storing all data/features to train the model
        self.retrain_interval = 10
        self.retrain_counter = 0
    
    def sort_orderbook(self, orderbook_data):
        # asks to be ascendingly sorted and bids to be descendingly sorted
        asks = np.array(orderbook_data.get('asks', []), dtype=float)
        bids = np.array(orderbook_data.get('bids', []), dtype=float)
        
        asks = asks[asks[:, 0].argsort()]
        bids = bids[bids[:, 0].argsort()[::-1]]

        return asks, bids
        
    def estimate_slippage(self, orderbook_data, order_type, quantity=100):
        """
        Estimate slippage in basis points for a given order.
        """
        if not orderbook_data or 'asks' not in orderbook_data or 'bids' not in orderbook_data:
            return {"predicted_slippage_bps": None, "error": "Invalid orderbook data"}
        
        start_time = time.time()
        asks_array, bids_array = self.sort_orderbook(orderbook_data)
        
        if not len(asks_array) or not len(bids_array):
            return {"predicted_slippage_bps": None, "error": "Empty orderbook"}

        best_ask = asks_array[0][0]
        best_bid = bids_array[0][0]
        
        mid_price = (best_ask + best_bid) / 2
        
        # considering that we are only acting as market maker
        # Initialize variables for walking the book
        remaining_usd = quantity
        total_btc_bought = 0.0
        total_usd_spent = 0.0
        
        # Walk up the ask side of the book
        for ask in asks_array:
            price = float(ask[0])
            size = float(ask[1])
            
            # Convert size to USD value
            level_usd = price * size
            
            if remaining_usd <= 0:
                break
                
            # If this level can fill the remaining quantity
            if level_usd >= remaining_usd:
                total_btc_bought += size
                total_usd_spent += level_usd
                remaining_usd -= level_usd
            else:
                # Partial fill at this level
                partial_btc = remaining_usd / price
                total_btc_bought += partial_btc
                total_usd_spent += remaining_usd
                remaining_usd = 0
                break
        
        # If no BTC bought, return error
        if total_btc_bought == 0:
            return {"predicted_slippage_bps": None, "error": "Quantity too low for market depth"}

        # Calculate actual average execution price in USD
        avg_execution_price = total_usd_spent / total_btc_bought

        # Slippage vs mid price
        slippage_bps = ((avg_execution_price - mid_price) / mid_price) * 10000

        # # Calculate slippage cost in USD
        # slippage_cost = quantity * (slippage_bps / 10000)
        
        # Spread
        spread = best_ask - best_bid
        spread_bps = (spread / mid_price) * 10000  # basis points
        
        # Depths
        ask_depth = np.sum(asks_array[:5, 1]) if len(asks_array) >= 5 else np.sum(asks_array[:, 1])
        bid_depth = np.sum(bids_array[:5, 1]) if len(bids_array) >= 5 else np.sum(bids_array[:, 1])
        
        # Imbalance
        imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
        
        # Features vector
        features = [spread_bps, ask_depth, bid_depth, imbalance, quantity]
        
        # Save to historical training data
        self.historical_data.append((features, slippage_bps))
        
        self.retrain_counter += 1

        if self.retrain_counter % self.retrain_interval == 0:
            X = np.array([x[0] for x in self.historical_data])
            y = np.array([x[1] for x in self.historical_data])
            self.model.fit(X, y)
        
        try:
            predicted_slippage = self.model.predict([features])[0]
        except Exception:
            predicted_slippage = slippage_bps  # Fallback to actual slippage if model not trained
        
        processing_time = time.time() - start_time
        
        return {
            "actual_slippage_bps": slippage_bps,
            "predicted_slippage_bps": predicted_slippage,
            "processing_time_ms": processing_time * 1000
        }

# Create a singleton instance
_estimator = SlippageEstimator()

def estimate_slippage(orderbook_data, order_type, quantity=100):
    """
    Estimate slippage for a given order.
    
    Args:
        orderbook_data (dict): The orderbook data
        order_type (str): The order type (market/limit)
        quantity (float): The order quantity in USD
        
    Returns:
        dict: Estimated slippage and related metrics
    """
    return _estimator.estimate_slippage(orderbook_data, order_type, quantity)
