import numpy as np
import time
import math

class MarketImpactModel:
    """
    Implementation of the Almgren-Chriss market impact model for estimating
    the price impact of executing orders in financial markets.
    
    The Almgren-Chriss model divides market impact into:
    1. Temporary impact: Immediate price changes during execution that recover afterward
    2. Permanent impact: Lasting price changes that remain after execution
    
    References:
    - Almgren, R., & Chriss, N. (2001). "Optimal execution of portfolio transactions"
    """
    
    def __init__(self):
        # Model parameters (these would typically be calibrated from market data)
        self.sigma = 0.3  # Daily volatility (annualized)
        self.T = 1/365    # Time horizon (fraction of a year, default: 1 day)
        self.eta = 1.5    # Temporary impact factor
        self.gamma = 0.1  # Permanent impact factor
        self.last_update_time = 0
        
    def update_parameters(self, volatility=None, time_horizon=None):
        """
        Update model parameters based on market conditions.
        
        Args:
            volatility (float): Market volatility (annualized)
            time_horizon (float): Time horizon in days
        """
        if volatility is not None:
            self.sigma = volatility
        
        if time_horizon is not None:
            self.T = time_horizon / 365  # Convert days to fraction of year
            
        self.last_update_time = time.time()
    
    def calculate_market_impact(self, orderbook_data, quantity, order_type="market"):
        """
        Calculate the expected market impact for a given order.
        
        Args:
            orderbook_data (dict): The orderbook data containing bids and asks
            quantity (float): The quantity to trade in USD
            order_type (str): The order type (market, limit, etc.)
            
        Returns:
            dict: Calculated market impact and related metrics
        """
        if not orderbook_data or 'asks' not in orderbook_data or 'bids' not in orderbook_data:
            return {"temporary_impact_bps": None, "permanent_impact_bps": None, "total_impact_bps": None, "error": "Invalid orderbook data"}
        
        # Record the time for performance metrics
        start_time = time.time()
        
        # Extract asks and bids
        asks = orderbook_data.get('asks', [])
        bids = orderbook_data.get('bids', [])
        
        if not asks or not bids:
            return {"temporary_impact_bps": None, "permanent_impact_bps": None, "total_impact_bps": None, "error": "Empty orderbook"}
        
        # Calculate mid price
        best_ask = float(asks[0][0])
        best_bid = float(bids[0][0])
        mid_price = (best_ask + best_bid) / 2
        
        # Calculate market depth and liquidity
        depth = 0
        for i in range(min(5, len(asks))):
            depth += float(asks[i][1])
        for i in range(min(5, len(bids))):
            depth += float(bids[i][1])
        
        # Convert quantity from USD to asset quantity
        asset_quantity = quantity / mid_price
        
        # Calculate average daily volume (ADV) - in a real system, this would come from historical data
        # Here we're estimating it based on the current orderbook depth
        estimated_adv = depth * 24 * 60  # Simple estimation: current depth * minutes in a day
        
        # Calculate participation rate (X/V in Almgren-Chriss model)
        participation_rate = asset_quantity / estimated_adv if estimated_adv > 0 else 0.01
        
        # Calculate temporary impact (immediate price change during execution)
        # Formula: η * σ * sqrt(T) * (X/V)^0.5
        temporary_impact = self.eta * self.sigma * math.sqrt(self.T) * math.sqrt(participation_rate)
        
        # Calculate permanent impact (lasting price change)
        # Formula: γ * σ * sqrt(T) * (X/V)
        permanent_impact = self.gamma * self.sigma * math.sqrt(self.T) * participation_rate
        
        # Convert impact to basis points
        temporary_impact_bps = temporary_impact * 10000
        permanent_impact_bps = permanent_impact * 10000
        total_impact_bps = temporary_impact_bps + permanent_impact_bps
        
        processing_time = time.time() - start_time
        
        return {
            "temporary_impact_bps": temporary_impact_bps,
            "permanent_impact_bps": permanent_impact_bps,
            "total_impact_bps": total_impact_bps,
            "mid_price": mid_price,
            "participation_rate": participation_rate,
            "processing_time_ms": processing_time * 1000
        }

# Create a singleton instance for the application to use
_model = MarketImpactModel()

def update_market_impact_parameters(volatility=None, time_horizon=None):
    """
    Update the market impact model parameters.
    
    Args:
        volatility (float): Market volatility (annualized)
        time_horizon (float): Time horizon in days
    """
    _model.update_parameters(volatility, time_horizon)

def calculate_market_impact(orderbook_data, quantity=100, order_type="market"):
    """
    Calculate market impact for a given order.
    
    Args:
        orderbook_data (dict): The orderbook data
        quantity (float): The quantity in USD
        order_type (str): The order type
        
    Returns:
        dict: Calculated market impact and related metrics
    """
    return _model.calculate_market_impact(orderbook_data, quantity, order_type)
