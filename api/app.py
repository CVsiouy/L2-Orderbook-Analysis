import eventlet
eventlet.monkey_patch()
import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from loguru import logger

# Import websocket handler and models
from websocket_handler import start_websocket, get_latest_orderbook, get_connection_status, subscribe, unsubscribe
from models.slippage_model import estimate_slippage
from models.market_impact_model import calculate_market_impact, update_market_impact_parameters
from models.maker_taker_model import predict_maker_taker
from models.fees_latency_model import calculate_fees, track_processing_time, get_latency_metrics, reset_latency_metrics

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{message}</level>")
logger.add("logs/app.log", rotation="10 MB", retention="7 days", compression="zip")

# Initialize Flask app and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global variables for tracking parameters and analytics
current_params = {
    "exchange": "OKX",
    "symbol": "BTC-USDT-SWAP",
    "order_type": "Market",
    "quantity": 100,
    "volatility": 0.3,
    "fee_tier": "VIP0"
}

# Start websocket connection in a separate thread
logger.info("Starting WebSocket connection thread...")
eventlet.spawn(start_websocket)

def calculate_analytics(orderbook_data, params):
    """
    Calculate all analytics based on orderbook data and parameters.
    
    Args:
        orderbook_data (dict): The orderbook data
        params (dict): The parameters for calculation
        
    Returns:
        dict: Calculated analytics
    """
    if not orderbook_data or 'asks' not in orderbook_data or 'bids' not in orderbook_data:
        return {
            "error": "Invalid orderbook data",
            "timestamp": time.time()
        }
    
    start_time = time.time()
    
    try:
        # Extract parameters
        order_type = params.get('order_type', 'market')
        quantity = float(params.get('quantity', 100))
        volatility = float(params.get('volatility', 0.3))
        fee_tier = params.get('fee_tier', 'VIP0')
        
        # Update model parameters
        update_market_impact_parameters(volatility=volatility)
        
        # Calculate slippage
        slippage_result = estimate_slippage(orderbook_data, order_type, quantity)
        
        # Calculate market impact
        impact_result = calculate_market_impact(orderbook_data, quantity, order_type)
        
        # Predict maker/taker proportion
        maker_taker_result = predict_maker_taker(orderbook_data, quantity, order_type)
        
        # Calculate fees
        maker_ratio = maker_taker_result.get('maker_ratio', 0)
        taker_ratio = maker_taker_result.get('taker_ratio', 1)
        fee_result = calculate_fees(quantity, fee_tier, maker_ratio, taker_ratio)
        
        # Calculate net cost
        slippage_bps = slippage_result.get('predicted_slippage_bps', 0)
        impact_bps = impact_result.get('total_impact_bps', 0)
        
        # Convert basis points to percentage
        slippage_cost = quantity * (slippage_bps / 10000)
        impact_cost = quantity * (impact_bps / 10000)
        fee_amount = fee_result.get('amount', 0)
        
        net_cost = slippage_cost + impact_cost + fee_amount
        net_cost_bps = (net_cost / quantity) * 10000 if quantity > 0 else 0
        
        # Calculate processing time
        processing_time = time.time() - start_time
        track_processing_time(processing_time)
        
        # Prepare analytics result
        result = {
            "exchange": params.get('exchange', 'OKX'),
            "symbol": params.get('symbol', 'BTC-USDT-SWAP'),
            "order_type": order_type,
            "quantity": quantity,
            "slippage": {
                "bps": slippage_bps,
                "cost": slippage_cost
            },
            "market_impact": {
                "temporary_bps": impact_result.get('temporary_impact_bps', 0),
                "permanent_bps": impact_result.get('permanent_impact_bps', 0),
                "total_bps": impact_bps,
                "cost": impact_cost
            },
            "fees": {
                "maker_rate": fee_result.get('maker_rate', 0),
                "taker_rate": fee_result.get('taker_rate', 0),
                "weighted_rate": fee_result.get('weighted_rate', 0),
                "amount": fee_amount
            },
            "maker_taker": {
                "maker_ratio": maker_ratio,
                "taker_ratio": taker_ratio
            },
            "net_cost": {
                "amount": net_cost,
                "bps": net_cost_bps
            },
            "latency": {
                "processing_time_ms": processing_time * 1000
            },
            "timestamp": time.time()
        }
        
        return result
    except Exception as e:
        logger.error(f"Error calculating analytics: {str(e)}")
        return {
            "error": f"Error calculating analytics: {str(e)}",
            "timestamp": time.time()
        }

def on_orderbook_update(data):
    """
    Handle orderbook updates and calculate analytics.
    
    Args:
        data (dict): The orderbook update event
    """
    try:
        orderbook_data = data.get('data')
        if not orderbook_data:
            return
        
        # Calculate analytics with current parameters
        analytics = calculate_analytics(orderbook_data, current_params)
        
        # Emit analytics update to all clients
        socketio.emit('analytics_update', analytics)
    except Exception as e:
        logger.error(f"Error handling orderbook update: {str(e)}")
        socketio.emit('error', {
            "code": "ANALYTICS_ERROR",
            "message": f"Error calculating analytics: {str(e)}"
        })

# Subscribe to orderbook updates
subscribe(on_orderbook_update)

@socketio.on('connect')
def handle_connect():

    logger.info('Client connected')
    
    # Send connection status
    status = get_connection_status()
    emit('connection_status', status)
    
    # Send current parameters
    emit('parameter_update', current_params)
    
    # Send latest orderbook if available
    orderbook = get_latest_orderbook()
    if orderbook:
        emit('orderbook_update', orderbook)
        
        # Calculate and send initial analytics
        analytics = calculate_analytics(orderbook, current_params)
        emit('analytics_update', analytics)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

@socketio.on('parameter_update')
def handle_parameter_update(data):
    """
    Handle parameter updates from clients.
    
    Args:
        data (dict): The updated parameters
    """
    global current_params
    
    try:
        logger.info(f"Received parameter update: {data}")
        
        # Update current parameters
        for key, value in data.items():
            if key in current_params:
                # Convert numeric values
                if key in ['quantity', 'volatility']:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        emit('error', {
                            "code": "PARAMETER_ERROR",
                            "message": f"Invalid value for {key}: {value}"
                        })
                        continue
                
                current_params[key] = value
        
        # Broadcast updated parameters to all clients
        socketio.emit('parameter_update', current_params)
        
        # Recalculate analytics with new parameters
        orderbook = get_latest_orderbook()
        if orderbook:
            analytics = calculate_analytics(orderbook, current_params)
            socketio.emit('analytics_update', analytics)
    except Exception as e:
        logger.error(f"Error handling parameter update: {str(e)}")
        emit('error', {
            "code": "PARAMETER_UPDATE_ERROR",
            "message": f"Error updating parameters: {str(e)}"
        })

@socketio.on_error_default
def default_error_handler(e):
    """Handle SocketIO errors."""
    logger.error(f"SocketIO Error: {str(e)}")
    socketio.emit('error', {
        "code": "SOCKET_ERROR",
        "message": f"SocketIO Error: {str(e)}"
    })

if __name__ == '__main__':
    try:
        logger.info("Starting SocketIO server...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
