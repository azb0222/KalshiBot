**TODO**
- make into Python package
- implement rate limiting 
- update the Dockerfile 
- update PennyBot structure to have a MarketTrader class 

```
import os
import asyncio
# Other imports...

class MarketTrader:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api_client = None
        self.token = None

    async def login(self):
        # Implement login logic and set self.token

    async def wait_for_market_open(self):
        # Implement waiting logic

    def get_account_balance(self):
        # Return account balance

    async def start_trading(self):
        # Main trading logic including WebSocket connection

def main():
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")
    trader = MarketTrader(email, password)
    asyncio.run(trader.start())

if __name__ == "__main__":
    main()
```

- implement Juypter Notebook for visualization, expose Notebook 
- import into EC2
- cron job to run script during trading hours only 


**Bot Architecture**

As reccomended by the Kalshi API documentation:
- We are using the Kalshi Websocket to fetch a live stream of market data 
- We are using Kalshi REST API for trading 