from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(filename='trades.log', level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_mt5():
    """Initialize MetaTrader5 connection."""
    if not mt5.initialize(login=204242456, server="Exness-MT5Trial7", password="Ntr@60097"):
        logging.error("MT5 initialization failed")
        return False
    logging.info("MT5 initialized successfully")
    return True

def place_trade(symbol, side, entry, sl, tp, lot=0.1):
    """Place a trade using MetaTrader5."""
    if not mt5.initialize():
        logging.error("MT5 initialization failed")
        return False

    # Prepare trade request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if side.lower() == "buy" else mt5.ORDER_TYPE_SELL,
        "price": entry,
        "sl": sl,
        "tp": tp,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    # Send trade request
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Trade failed: {result.comment}")
        return False

    logging.info(f"Trade placed: {result.order} | {symbol} {side} @ {entry}")
    return True

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from TradingView."""
    try:
        data = request.json
        logging.info(f"Received webhook: {data}")

        # Extract fields
        symbol = data.get('symbol')
        side = data.get('side')
        entry = float(data.get('entry'))
        sl = float(data.get('sl'))
        tp = float(data.get('tp'))

        # Validate data
        if not all([symbol, side, entry, sl, tp]):
            logging.error("Invalid webhook data")
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Place trade
        if place_trade(symbol, side, entry, sl, tp):
            return jsonify({"status": "success", "message": "Trade placed"}), 200
        else:
            return jsonify({"status": "error", "message": "Trade failed"}), 500

    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    if initialize_mt5():
        app.run(host="0.0.0.0", port=5000)
    else:
        logging.error("Bot failed to start due to MT5 initialization error")
