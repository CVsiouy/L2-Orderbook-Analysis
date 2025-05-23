import numpy as np
import time
from sklearn.linear_model import LogisticRegression
from collections import Counter


class MakerTakerModel:
    """
    Model to predict the maker/taker proportion for a given order based on
    orderbook conditions and order parameters.
    
    This model uses logistic regression to estimate the probability that
    an order will be filled as a maker (providing liquidity) vs. taker
    (consuming liquidity).
    """
    
    def __init__(self):
        # Initialize logistic regression model
        self.model = LogisticRegression(random_state=42)
        self.is_trained = False
        self.historical_data = []
        self.prediction_counter = 0
    
    def _extract_features(self, orderbook_data, order_size):
        """
        Extract relevant features from orderbook data for maker/taker prediction.
        
        Args:
            orderbook_data (dict): The orderbook data
            order_size (float): The order size in USD
            
        Returns:
            dict: Extracted features
        """
        asks = orderbook_data.get('asks', [])
        bids = orderbook_data.get('bids', [])
        
        if not asks or not bids:
            return {
                'spread': 1.0,
                'depth_ratio': 1.0,
                'relative_size': 1.0,
                'price_range': 1.0,
                'imbalance': 0.0
            }
        
        # Calculate basic orderbook metrics
        best_ask = float(asks[0][0])
        best_bid = float(bids[0][0])
        mid_price = (best_ask + best_bid) / 2
        
        # Calculate spread in basis points
        spread = (best_ask - best_bid) / mid_price
        
        # Calculate depth
        ask_depth = sum(float(size) for _, size in asks[:5])
        bid_depth = sum(float(size) for _, size in bids[:5])
        total_depth = ask_depth + bid_depth
        
        # Calculate depth ratio
        depth_ratio = bid_depth / ask_depth if ask_depth > 0 else 1.0
        
        # Calculate order size relative to available liquidity
        relative_size = (order_size / mid_price) / total_depth if total_depth > 0 else 1.0
        
        # Calculate price range (volatility indicator)
        ask_prices = [float(price) for price, _ in asks[:5]]
        bid_prices = [float(price) for price, _ in bids[:5]]
        price_range = (max(ask_prices) - min(bid_prices)) / mid_price if bid_prices and ask_prices else 1.0
        
        # Calculate imbalance
        imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
        
        return {
            'spread': spread,
            'depth_ratio': depth_ratio,
            'relative_size': relative_size,
            'price_range': price_range,
            'imbalance': imbalance
        }
    
    def _train_model(self):
        """Train the maker/taker model using historical data."""
        if len(self.historical_data) < 10:
            return
        
        # Extract features and labels for training
        X = np.array([
            [
                d['features']['spread'],
                d['features']['depth_ratio'],
                d['features']['relative_size'],
                d['features']['price_range'],
                d['features']['imbalance']
            ]
            for d in self.historical_data
        ])
        
        print(Counter([d['label'] for d in self.historical_data]))

        
        # For binary classification, we'd use 0/1 labels
        # For regression of maker probability, we'd use continuous values
        # y = np.array([d['maker_prob'] > 0.5 for d in self.historical_data])
        # print(y)
        
        y = np.array([d['label'] for d in self.historical_data])
        
        classes, counts = np.unique(y, return_counts = True)
        if len(classes)<2:
            print(f"Skipping training: only one class present: {dict(zip(classes, counts))}")
            return
        
        # Check for at least two classes
        # class_counts = Counter(y)
        # if len(class_counts) < 2:
        #     print(f"Skipping training: only one class in data: {class_counts}")
        #     return
        
        # Train the model
        try:
            self.model.fit(X, y)
            self.is_trained = True
        except Exception as e:
            print(f"Error training maker/taker model: {str(e)}")
    
    def predict_maker_taker(self, orderbook_data, order_size, order_type="market"):
        """
        Predict the maker/taker proportion for a given order.
        
        Args:
            orderbook_data (dict): The orderbook data
            order_size (float): The order size in USD
            order_type (str): The order type
            
        Returns:
            dict: Predicted maker/taker proportion and related metrics
        """
        if not orderbook_data or 'asks' not in orderbook_data or 'bids' not in orderbook_data:
            return {"maker_ratio": 0.0, "taker_ratio": 1.0, "error": "Invalid orderbook data"}
        
        # Record the time for performance metrics
        start_time = time.time()
        
        # For market orders, assume 100% taker
        if order_type == "market":
            processing_time = time.time() - start_time
            return {
                "maker_ratio": 0.0,
                "taker_ratio": 1.0,
                "confidence": 0.95,
                "processing_time_ms": processing_time * 1000
            }
        
        # Extract features
        features = self._extract_features(orderbook_data, order_size)
        
        spread = features['spread']
        relative_size = features['relative_size']
        
        # print("spread: ", spread, " ", "relative_size ", relative_size)
        
        maker_prob_heuristic = 1.0 / (1.0 + np.exp(5 * (relative_size - 0.2)))
        maker_prob_heuristic *= 1.0 / (1.0 + np.exp(5 * (spread - 0.0001)))
        
        # print(f"maker_prob_heuristic={maker_prob_heuristic}, spread={spread}, relative_size={relative_size}")
        

        
        label = int(np.random.rand() < maker_prob_heuristic)


        # Store data for training
        self.historical_data.append({
            'features': features,
            'label': label
        })
        
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]
            
        self.prediction_counter += 1
        if self.prediction_counter % 10 == 0:
            self._train_model()
            
            

        # Predict using model if trained
        if self.is_trained:
            X = np.array([[
                features['spread'],
                features['depth_ratio'],
                features['relative_size'],
                features['price_range'],
                features['imbalance']
            ]])
            maker_prob = self.model.predict_proba(X)[0][1]
        else:
            maker_prob = maker_prob_heuristic

        if order_type == "limit":
            maker_prob = 0.7 * maker_prob + 0.3
        taker_prob = 1.0 - maker_prob
        
        return {
            "maker_ratio": maker_prob,
            "taker_ratio": taker_prob,
            "confidence": 0.8,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        
# Create a singleton instance for the application to use
_model = MakerTakerModel()

def predict_maker_taker(orderbook_data, order_size=100, order_type="market"):
    """
    Predict maker/taker proportion for a given order.
    
    Args:
        orderbook_data (dict): The orderbook data
        order_size (float): The order size in USD
        order_type (str): The order type
        
    Returns:
        dict: Predicted maker/taker proportion and related metrics
    """
    return _model.predict_maker_taker(orderbook_data, order_size, order_type)
