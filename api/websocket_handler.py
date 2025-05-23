import websocket
import json
import threading
import time
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{message}</level>")
logger.add("logs/websocket_handler.txt", rotation="10 MB", retention="7 days", compression="zip")

latest_orderbook = None
connection_active = False
last_update_time = 0
orderbook_subscribers = []

def on_message(ws, message):
    """
    Get the latest orderbook data from the WebSocket connection.
    
    Action:
        send the orderbook to global orderbook variable, additionally check for any json ping that can bypass protocol layer 
    """
    
    if message.strip() in ('ping', 'pong'):
        logger.debug("Received ping/pong message")
        return

    global latest_orderbook, last_update_time
    
    try:
        data = json.loads(message)
        # print(data) - checking if getting data
        # Store the latest orderbook data
        latest_orderbook = data
        last_update_time = time.time()
        logger.debug(f"Received orderbook update for {data.get('symbol', 'unknown')}")
        
        # Notify all subscribers about the new orderbook data
        notify_subscribers(data)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode message: {message[:100]}...")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

def on_error(ws, error):
    logger.error(f"WebSocket error: {error}")
    # Notify subscribers about the error
    notify_error("ORDERBOOK_CONNECTION_ERROR", str(error))

def on_close(ws, close_status_code, close_msg):
    global connection_active
    connection_active = False
    logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    # Notify subscribers about the connection closure
    notify_connection_status()

def on_open(ws):
    global connection_active
    connection_active = True
    logger.info("WebSocket connection opened")
    # Notify subscribers about the connection status
    notify_connection_status()

def start_websocket():
    global connection_active
    websocket.enableTrace(False)
    
    while True:
        try:
            if not connection_active:
                logger.info("Attempting to connect to WebSocket...")
                ws = websocket.WebSocketApp(
                    "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP",
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                ws.run_forever()
            
            # If connection drops, wait before reconnecting
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
            notify_error("ORDERBOOK_CONNECTION_ERROR", str(e))
            time.sleep(1)

def get_latest_orderbook():
    """
    Returns the latest orderbook data received from the WebSocket.
    
    Returns:
        dict: The latest orderbook data or None if no data has been received yet.
    """
    global latest_orderbook
    return latest_orderbook

def get_connection_status():
    """
    Returns the current connection status and time since last update.
    
    Returns:
        dict: Connection status information
    """
    global connection_active, last_update_time
    current_time = time.time()
    time_since_update = current_time - last_update_time if last_update_time > 0 else None
    
    return {
        "connected": connection_active,
        "last_update": last_update_time,
        "time_since_update": time_since_update
    }

def subscribe(callback):
    """
    Subscribe to orderbook updates.
    
    Args:
        callback: Function to call with orderbook updates
    """
    if callback not in orderbook_subscribers:
        orderbook_subscribers.append(callback)
        logger.info(f"New subscriber added. Total subscribers: {len(orderbook_subscribers)}")
        
        # Send initial data if available
        if latest_orderbook:
            try:
                callback({"event": "orderbook_update", "data": latest_orderbook})
            except Exception as e:
                logger.error(f"Error notifying subscriber: {str(e)}")
        
        # Send connection status
        status = get_connection_status()
        try:
            callback({"event": "connection_status", "data": status})
        except Exception as e:
            logger.error(f"Error sending connection status: {str(e)}")

def unsubscribe(callback):
    """
    Unsubscribe from orderbook updates.
    
    Args:
        callback: Function to unsubscribe
    """
    if callback in orderbook_subscribers:
        orderbook_subscribers.remove(callback)
        logger.info(f"Subscriber removed. Total subscribers: {len(orderbook_subscribers)}")

def notify_subscribers(data):
    """
    Notify all subscribers about new orderbook data.
    
    Args:
        data: Orderbook data to send
    """
    message = {"event": "orderbook_update", "data": data}
    for callback in orderbook_subscribers[:]:  # Create a copy to avoid modification during iteration
        try:
            callback(message)
        except Exception as e:
            logger.error(f"Error notifying subscriber: {str(e)}")
            # Consider removing failed subscribers
            # orderbook_subscribers.remove(callback)

def notify_connection_status():
    """
    Notify all subscribers about connection status changes.
    """
    status = get_connection_status()
    message = {"event": "connection_status", "data": status}
    for callback in orderbook_subscribers[:]:
        try:
            callback(message)
        except Exception as e:
            logger.error(f"Error sending connection status: {str(e)}")

def notify_error(code, message):
    """
    Notify all subscribers about an error.
    
    Args:
        code: Error code
        message: Error message
    """
    error_data = {"event": "error", "data": {"code": code, "message": message}}
    for callback in orderbook_subscribers[:]:
        try:
            callback(error_data)
        except Exception as e:
            logger.error(f"Error sending error notification: {str(e)}")
