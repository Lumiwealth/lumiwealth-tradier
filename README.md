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
      
      `from lumiwealth-tradier import Tradier, Account, Quotes, EquityOrder, OptionsData, OptionsOrder`
      
      `dotenv.load_dotenv()`
      
      `tradier_acct = os.getenv('tradier_acct')`
      
      `tradier_token = os.getenv('tradier_token')`
    
  * To instantiate the class objects, use: <br>
      `tradier = Tradier(tradier_acct, tradier_token)`

      `account = Account(tradier_acct, tradier_token)`

      `quotes = Quotes(tradier_acct, tradier_token)`

      `equity_order = EquityOrder(tradier_acct, tradier_token)`

      `options_data = OptionsData(tradier_acct, tradier_token`

      `options_order = OptionsOrder(tradier_acct, tradier_token)`

## Usage

This section provides example functionality of the existing codebase. Additional sample code demonstrating usage can be found in the `/examples/` directory.

### Account Management

- Get User Profile:

  `user_profile = account.get_user_profile()`

- Get Account Balance:

  `account_balance = account.get_account_balance()`

- Get Gain/Loss:

  `gain_loss = account.get_gainloss()`

- Get Orders:

  `orders = account.get_orders()`

- Get Positions:

  `positions = account.get_positions()`

### Trading

- Place Equity Order:

  `order_response = equity_order.place_order('AAPL', 'buy', 1, 'limit', 150)`

- Place Options Order:

  `order_response = options_order.place_order('AAPL210917C00125000', 'buy_to_open', 1, 'limit', 3.5)`

### Market Data

- Get Quotes:

  `quotes_data = quotes.get_quote_day('AAPL')`

- Get Historical Quotes:

  `historical_data = quotes.get_historical_quotes('AAPL')`

- Get Time Sales:

  `timesales = quotes.get_timesales('AAPL')`

### Options Data

- Get Options Chains:

  `options_chains = options_data.get_options_chain('AAPL')`

- Get Options Strikes:

  `options_strikes = options_data.get_options_strikes('AAPL')`

- Get Options Expirations:

  `options_expirations = options_data.get_options_expirations('AAPL')`

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
