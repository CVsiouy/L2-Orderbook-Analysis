# Flask + React App

## Backend (Flask)
- Python 3.x
- Flask
- socketio

### Setup

#### Backend for windows
```bash
cd api
python -m venv venv
.venv/Scripts/activate
pip install -r requirements.txt
python app.py
```
venv setup for MacOS - source venv/bin/activate

#### Frontend
Please start a new Terminal
```bash
npm run dev
```

The Project Uses websocket provided by GoQuant through OKX Exchange to access Tick by Tick L2 Orderbook data of BTC/USDT Spot Asset.
The goal was to access and utilize the tick-by-tick L2 orderbook bids and asks data and apply financial models such as Almgren-Chriss Model,
Calculate Slippage using Linear Regression and estimate maker/Taker Proportion on the Live Data and Display Live Analytics on our Frontend based 
on our input parameters.

Additionally use OKX documentation for calculating Fees for different premium tiers(VIP0 to VIP5) and their impact on net cost to buy a 
fixed amount of asset in USD due to changing maker/taker fee based on tier.

Initially the project used REST API via websocket and threading and later implemented flask-socketio and eventlet to continously update our frontend.

### Future Optimization
1. Ensure procuring a websocket connection without any middleman involved.
2. Use FastAPI and Numba and LRU cache to make Calculation Faster.
3. Read Research Paper on implementing Dynamic Programming on Almgren-Chriss Model instead of our Non-linear Model. (Some Quantity issue was Observed in DP)
4. Improve UI and Add more functionalities.

###
To run on your localhost kindly create a .env file for VITE_SOCKET_URL = (your_localhost_server)






