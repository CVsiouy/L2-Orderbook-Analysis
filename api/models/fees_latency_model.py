import time
from collections import deque

class FeesCalculator:
    """
    Rule-based fee calculator for trading fees based on exchange fee tiers
    and maker/taker proportions.
    """
    
    def __init__(self):
        # Fee rates for different tiers (maker/taker)
        self.fee_rates = {
            'VIP0': {'maker': 0.0008, 'taker': 0.0010},
            'VIP1': {'maker': 0.0007, 'taker': 0.0009},
            'VIP2': {'maker': 0.0006, 'taker': 0.0008},
            'VIP3': {'maker': 0.0005, 'taker': 0.0007},
            'VIP4': {'maker': 0.0004, 'taker': 0.0006},
            'VIP5': {'maker': 0.0002, 'taker': 0.0004},
        }
        self.last_update_time = 0
    
    def calculate_fees(self, quantity, fee_tier, maker_ratio, taker_ratio):
        """
        Calculate trading fees based on quantity, fee tier, and maker/taker proportion.
        
        Args:
            quantity (float): Order quantity in USD
            fee_tier (str): Fee tier (e.g., 'VIP0', 'VIP1', etc.)
            maker_ratio (float): Proportion of order expected to be maker (0-1)
            taker_ratio (float): Proportion of order expected to be taker (0-1)
            
        Returns:
            dict: Calculated fees and related metrics
        """
        start_time = time.time()
        
        # Get fee rates for the specified tier (default to VIP0 if not found)
        fee_rate = self.fee_rates.get(fee_tier, self.fee_rates['VIP0'])
        
        # Calculate weighted fee based on maker/taker proportion
        weighted_fee_rate = (maker_ratio * fee_rate['maker']) + (taker_ratio * fee_rate['taker'])
        
        # Calculate fee amount
        fee_amount = quantity * weighted_fee_rate
        
        processing_time = time.time() - start_time
        self.last_update_time = time.time()
        
        return {
            "maker_rate": fee_rate['maker'],
            "taker_rate": fee_rate['taker'],
            "weighted_rate": weighted_fee_rate,
            "amount": fee_amount,
            "processing_time_ms": processing_time * 1000
        }

class LatencyTracker:
    """
    Tracks and calculates internal latency metrics for the trading system.
    """
    
    def __init__(self, max_samples=100):
        self.processing_times = deque(maxlen=max_samples)
        self.ui_update_times = deque(maxlen=max_samples)
        self.total_latency = deque(maxlen=max_samples)
        self.last_update_time = 0
    
    def add_processing_time(self, processing_time):
        """
        Add a processing time measurement.
        
        Args:
            processing_time (float): Processing time in seconds
        """
        self.processing_times.append(processing_time)
        self.last_update_time = time.time()
    
    def add_ui_update_time(self, ui_update_time):
        """
        Add a UI update time measurement.
        
        Args:
            ui_update_time (float): UI update time in seconds
        """
        self.ui_update_times.append(ui_update_time)
    
    def add_total_latency(self, total_latency):
        """
        Add a total latency measurement.
        
        Args:
            total_latency (float): Total latency in seconds
        """
        self.total_latency.append(total_latency)
    
    def get_metrics(self):
        """
        Get current latency metrics.
        
        Returns:
            dict: Latency metrics
        """
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        avg_ui_update_time = sum(self.ui_update_times) / len(self.ui_update_times) if self.ui_update_times else 0
        avg_total_latency = sum(self.total_latency) / len(self.total_latency) if self.total_latency else 0
        
        return {
            "avg_processing_time_ms": avg_processing_time * 1000,
            "avg_ui_update_time_ms": avg_ui_update_time * 1000,
            "avg_total_latency_ms": avg_total_latency * 1000,
            "processing_time_samples": len(self.processing_times),
            "last_processing_time_ms": (self.processing_times[-1] * 1000) if self.processing_times else 0
        }
    
    def reset(self):
        """Reset all latency metrics."""
        self.processing_times.clear()
        self.ui_update_times.clear()
        self.total_latency.clear()
        self.last_update_time = time.time()

# Create singleton instances
_fees_calculator = FeesCalculator()
_latency_tracker = LatencyTracker()

def calculate_fees(quantity, fee_tier, maker_ratio, taker_ratio):
    """
    Calculate trading fees.
    
    Args:
        quantity (float): Order quantity in USD
        fee_tier (str): Fee tier
        maker_ratio (float): Maker proportion
        taker_ratio (float): Taker proportion
        
    Returns:
        dict: Calculated fees and related metrics
    """
    return _fees_calculator.calculate_fees(quantity, fee_tier, maker_ratio, taker_ratio)

def track_processing_time(processing_time):
    """
    Track processing time.
    
    Args:
        processing_time (float): Processing time in seconds
    """
    _latency_tracker.add_processing_time(processing_time)

def get_latency_metrics():
    """
    Get current latency metrics.
    
    Returns:
        dict: Latency metrics
    """
    return _latency_tracker.get_metrics()

def reset_latency_metrics():
    """Reset all latency metrics."""
    _latency_tracker.reset()
