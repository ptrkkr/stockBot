# stockBot
Script which informs you about your stocks. 
This script was actually build quick and dirty, but it does its job!

## Setup
* Fill 'CHANGE-ME' fields (if not gmail account change 'SMTP_SERVER' also)
* For 'FREE_CURRENCY_API_KEY' got to https://free.currencyconverterapi.com/ and get a free key
* Change 'LIST_OF_E_MAILS' to the email addresses you want to inform
* Change 'STOCKS_LIST' to the stocks you want to get informed about
* Change 'UPDATE_PERIOD' to an interval (minutes) in which you want to get informed about your stocks
* Change 'IMPORTANT_CHANGE_THRESHOLD' to a percentage (e.g '5') where you want to get <i>emergency</i> updates about your stock
* Set up a cron to run this script
    * Example: <code>*/5 9-22 * * 1-5 cd path/to/folder/of/script; python3 stockBot.py >> log.txt 2>&1;</code>
* Change 'CONVERSION_FROM_TO' to the currencies you want to
* Change 'PRE_MARKET_START', 'REGULAR_MARKET_START' and 'REGULAR_MARKET_END' according to your timezone

## Information
I am going to improve the code if I have time to.<br>
Improvements:
* Cron lib in python
* Dynamically currency conversion
* More user-friendly script (run and configure all from commandline)
* Get pre-market by stock ticker and not by web scrapping yahoo finance
* Better logging

I do not know if the script works for everyone as well as it does for me, but it would make me very happy.
