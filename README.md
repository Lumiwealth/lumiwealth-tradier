# lumiwealth-tradier

`lumiwealth-tradier` is a Python package that serves as a wrapper for the Tradier brokerage API. This package simplifies the process of making API requests, handling responses, and performing various trading and account management operations.

The package was originally developed by data science graduate students at the University of Virginia.

## Features

- **Account Management**: Retrieve profile, balance, gain/loss, orders, and positions related to a trading account.
- **Trading**: Place, modify, and cancel equity and option orders.
- **Market Data**: Access real-time and historical market data for equities and options.
- **Options Data**: Retrieve options chains, strikes, and expiration dates.

## Installation

To install `lumiwealth-tradier`, you can use `pip`:

`pip install lumiwealth-tradier`

## Hello World

Steps to get started:
  * Create an account with <a href='https://tradier.com/'>Tradier.com</a>.
  * Grab Account Number and Access Token from your Tradier dashboard.
    * Log into Tradier > Preferences (gear icon) > API Access (left panel) > Sandbox Account Access (section).
  * Create a `.env` file in the appropriate working directory on your computer.
    * Launch text editor application.
    * Save the file as `.env`.
    * In the file, add the following lines, replacing the appropriate placeholder fields: <br>
        `tradier_acct=<YOUR_ACCOUNT_NUMBER_FROM_TRADIER_DASHBOARD>`

        `tradier_token=<YOUR_ACCESS_TOKEN_FROM_TRADIER_DASHBOARD>`
  * Within the aforementioned working directory, initiate a new python session (interactive python, jupyter notebook, etc.).
  * To authenticate yourself, add the following lines of code to the top of your python script or jupyter notebook: <br>    
      `import os, dotenv`

      `from lumiwealth_tradier import Tradier`
            
      `dotenv.load_dotenv()`
      
      `tradier_acct = os.getenv('tradier_acct')`
      
      `tradier_token = os.getenv('tradier_token')`
    
  * To instantiate the class objects, use: <br>
      `tradier = Tradier(tradier_acct, tradier_token, is_paper=True) # is_paper=True for sandbox environment, if you have a real money account, set to False`

## Usage

This section provides example functionality of the existing codebase. Additional sample code demonstrating usage can be found in the `/examples/` directory.

### Account Management

- Get User Profile:

  `user_profile = tradier.account.get_user_profile()`

- Get Account Balance:

  `account_balance = tradier.account.get_account_balance()`

- Get Gain/Loss:

  `gain_loss = tradier.account.get_gainloss()`

- Get Orders:

  `orders = tradier.orders.get_orders()`

- Get Positions:

  `positions = tradier.account.get_positions()`

### Trading

- Place Equity Order:

  `order_response = tradier.orders.order('AAPL', 'buy', 1, 'limit', 150)`

- Place Options Order:

  `order_response = tradier.orders.order('AAPL210917C00125000', 'buy_to_open', 1, 'limit', 3.5)`

### Market Data

- Get Last Price:

  `last_price = tradier.market.get_last_price('SPY')`

- Get Quotes:

  `quotes_data = tradier.market.get_quotes(["AAPL", "MSFT", "SPY"])`

- Get Historical Quotes and Get Time Sales:

  ```python
  from datetime import datetime, timedelta

  start_date = datetime.now() - timedelta(days=10)
  end_date = datetime.now()

  historical_data = tradier.market.get_historical_quotes(
      "AAPL",
      interval="daily",  # Can be "daily", "weekly", or "monthly"
      start_date=start_date,
      end_date=end_date,
      session_filter="all",  # Can be "all" or "open"
  )

  timesales = tradier.market.get_timesales(
      "MSFT",
      interval=1,  # Can be 1, 5 or 15
      start_date=start_date,
      end_date=end_date,
      session_filter="all",  # Can be "all" or "open"
  )
  ```

  - Get Options Chains:

  ```python
  tradier.market.get_chains(symbol, expiration, greeks=True)
  ```

  - Get Options Expirations:
  
    ```python
    tradier.market.get_options_expirations(symbol, strikes=True)
    ```

## Development

To contribute or make changes to the `lumiwealth-tradier` package, feel free to create a fork, clone the fork, make some improvements and issue a pull request. From the terminal/command prompt:

- Clone the forked branch to your local machine:

  `git clone https://github.com/YOUR_USERNAME/lumiwealth-tradier.git`

- Navigate to the directory where the relevant code is kept: 

  `cd lumiwealth-tradier`

- If you need to be careful about dependencies, create a new Python virtual environment: <br>

  `python -m venv replace_this_with_desired_venv_name` [Mac] <br>
  
  `venv\Scripts\activate` [Windows]

## Questions?

Happy to help! Feel free to contact Robert Grzesik by email at <EMAIL?>. <br>
Thanks much in advance for your interest in using the package.

## License

`lumiwealth-tradier` is licensed under the Apache License 2.0
