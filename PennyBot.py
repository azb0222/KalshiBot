import uuid
import kalshi_python
from kalshi_python.models import *
from pprint import pprint
import json 
from websockets.sync.client import connect
from websockets.http import Headers
import websockets
import asyncio 

KALSHI_WEBSOCKET_URL = "wss://demo-api.kalshi.co/trade-api/ws/v2"
KALSHI_REST_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
CONTRACT_PURCHASE_COUNT = 100

#TODO: move to env variables
email = "asrithabodepudi@gmail.com"
password = "zuni497RANT!"

series_tickers = {
    "S&P_RANGE": "INX", 
    "S&P_UP": "INXZ", 
    "S&P_YEARLY": "INXY",
    "S&P_ABOVE_BELOW": "INXU"
}

def main(): 
    config = kalshi_python.Configuration()
    config.host = KALSHI_REST_API_URL
    kalshi_api_client = kalshi_python.ApiInstance(
        email=email,
        password=password,
        configuration=config,
    )
    body = { 
        'email': email, 
        'password': password,
    }   
    login_response = kalshi_api_client.login(body=body)
    bearer_token = login_response.token

    if not is_market_open(kalshi_api_client):
        return #TODO: adjust to wait until market is open

    account_balance = kalshi_api_client.get_balance()
    print("CURRENT ACCOUNT BALANCE:")
    print(account_balance)
    trading_balance = account_balance.balance * 0.10  #TODO: implement this check

    market_tickers = get_market_tickers(kalshi_api_client, series_tickers["S&P_RANGE"])

    asyncio.run(websocket_connect_with_auth(kalshi_api_client, bearer_token, market_tickers))


def is_market_open(api_client):
    return api_client.get_exchange_status() #TODO: adjust to check for stock market opening times

def get_market_tickers(api_client, series_ticker): 
    market_tickers = [] #TODO: filter out by including the current date
    markets_response = api_client.get_markets(series_ticker=series_ticker)
    for market in markets_response.markets: 
        market_tickers.append(market.ticker)
    print(market_tickers)
    return market_tickers


async def websocket_connect_with_auth(api_client, token, market_tickers):
    id = 1 #increment sequentially 
    ticker_request = { 
        "id": id, 
        "cmd": "subscribe", 
        "params": { 
            "channels": ["ticker"], 
            "market_tickers": market_tickers
        }
    }

    headers = Headers({"Authorization": f"Bearer {token}"})
    json_ticker_request = json.dumps(ticker_request)


    jumps = {}
    purchases = {}


    async with websockets.connect(KALSHI_WEBSOCKET_URL, extra_headers=headers) as websocket:
        await websocket.send(json_ticker_request)
        while True:
            response = await websocket.recv()
            print(f"< {response}")
            response_data = json.loads(response)

            if response_data['type'] == "ticker":
                print(f"< {response}")
                market_ticker = response_data['msg']['market_ticker']
                yes_bid = response_data['msg']['yes_bid']
                ts = response_data['msg']['ts']

                if market_ticker in purchases:
                    if yes_bid <= purchases[market_ticker]:
                        sellOrderResponse = reate_order(api_client, market_ticker, False, True, purchases[market_ticker]) #TODO: implement error handling
                        print("SOLD BAD")
                        print(f"< {sellOrderResponse}")
        
                else:
                    if market_ticker not in jumps:
                        jumps[market_ticker] = [[],[]] #TODO: make this into a tuple 
                    jumps[market_ticker][0].append(yes_bid) #price []
                    jumps[market_ticker][1].append(ts) # seconds [] 

                    rates = calculate_rate_of_change(jumps[market_ticker][0], jumps[market_ticker][1])
                    if rates:
                        last_rate_of_change = rates[-1][2]
                        if last_rate_of_change > 0.80:
                            buy_order_response = create_order(api_client, market_ticker, True, True, yes_bid)
                            purchases[market_ticker] = (buy_order_response.order.yes_price)
                            create_order(api_client, market_ticker, False, False, yes_bid+2)
                            print("BOUGHT")
                            print(f"< {buy_order_response}")

#TODO: fix this to not calculate all the back ones 
def calculate_rate_of_change(prices, times):
    rate_of_change_results = []

    for i in range(len(times)):
        for j in range(i + 1, len(times)):
            if times[j] - times[i] >= 4:
                rate_of_change = (prices[j] - prices[i]) / (times[j] - times[i])
                rate_of_change_results.append((times[i], times[j], rate_of_change))
                break  
    return rate_of_change_results

def create_order(api_client, market_ticker, is_buy, is_quick, price): 
    order_UUID = str(uuid.uuid4())
    order_response = api_client.create_order(CreateOrderRequest(
                        ticker=market_ticker,
                        action="buy" if is_buy else "sell", 
                        type="quick" if is_quick else "limit", 
                        yes_price=price, 
                        count=CONTRACT_PURCHASE_COUNT,
                        client_order_id=order_UUID,
                        side='yes',
    ))
    print(f"ORDER MADE:")
    print(order_response)
    return order_response




if __name__ == "__main__":
    main()

