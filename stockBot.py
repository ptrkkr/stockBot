#!/usr/bin/env python3
import math
from json.decoder import JSONDecodeError

import yfinance as stock
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import datetime as time
import requests
from bs4 import BeautifulSoup
import pprint
import operator


# TODO use lib to make cron in python...
PORT = 465
SMTP_SERVER = "smtp.gmail.com"
SENDER_EMAIL = "CHANGE-ME"
PASSWORD = "CHANGE-ME"

URL = 'https://finance.yahoo.com/quote/{}'
YAHOO_PRE_MARKET_SPAN = "C($primaryColor) Fz(24px) Fw(b)"

FREE_CURRENCY_API_KEY = "CHANGE-ME"
FREE_CURRENCY_URL = "https://free.currconv.com/api/v7/convert?apiKey={}&q={}&compact=ultra"
CONVERSION_FROM_TO = "USD_EUR"

LIST_OF_E_MAILS = ['CHANGE-ME', 'CHANGE-ME']
STOCKS_LIST = ['AMC', 'GME']

PRE_SUBJECT_TEMPLATE = "[{}% RULE - IMPORTANT!] "
SUBJECT_TEMPLATE = "{stock_name}: {stock_price}€ ({stock_change}%)"
MESSAGE_GREETING = "Hello," \
                   "\n\nI got following market prices for you:"
MESSAGE_CONTENT_TEMPLATE = "\n\n{stock_name}: {dollar}$" \
                           "\n{stock_name}-OLD: {old_dollar}$" \
                           "\n{stock_name}: {euro}€" \
                           "\n{stock_name}-OLD: {old_euro}€" \
                           "\nChange since last update: {stock_change}%"
MESSAGE_CLOSING = "\n\nBest regards, " \
                  "\nYour Stock-Bot"
SUBJECT_STOCK_LIMITS = 2


DELIMITER = "==================================================================================================="

UPDATE_PERIOD = 150
IMPORTANT_CHANGE_THRESHOLD = 5

# TODO get timezone new york maybe?
PRE_MARKET_START = time.datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
REGULAR_MARKET_START = time.datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
REGULAR_MARKET_END = time.datetime.now().replace(hour=22, minute=00, second=0, microsecond=0)

DATABASE = "database.json"
CHANGE_SINCE_LAST_UPDATE_KEY = "changeSinceLastUpdate"
MARKET_PRICE_KEY = "marketPrice"
MARKET_PRICE_OLD_KEY = "marketPrice_old"
STOCKS_KEY = "stocks"
LAST_UPDATE_KEY = "lastUpdate"
DATABASE_TEMPLATE = {STOCKS_KEY: {},
                     LAST_UPDATE_KEY: ""}


def get_current_market_price():
    now = time.datetime.now()
    stock_price_dic = {}
    is_pre_market = PRE_MARKET_START <= now <= REGULAR_MARKET_START

    for stock_name in STOCKS_LIST:
        if is_pre_market:
            try:
                # TODO get Premarket from stock ticker... so for "AMC" its "AH9" as far as i know
                stock_price_dic[stock_name] = get_pre_market_stock_price(stock_name)
                continue
            except AttributeError:
                print(
                    "Could not get pre market price for {}. Maybe it's a crypto currency. Instead i will take the "
                    "normal market price".format(
                        stock_name))

        stock_price_dic[stock_name] = get_regular_market_price(stock_name)

    return stock_price_dic


def get_pre_market_stock_price(stock_name):
    page = requests.get(URL.format(stock_name))
    soup = BeautifulSoup(page.content, 'html.parser')
    price_span = soup.find("span", class_=YAHOO_PRE_MARKET_SPAN)

    return float(price_span.text)


def get_regular_market_price(stock_name):
    stock_infos = stock.Ticker(stock_name)

    return stock_infos.info['regularMarketPrice']


def persist_market_price(json_data):
    with open(DATABASE, "w") as write_file:
        json.dump(json_data, write_file)
        return json_data


# TODO refactor
def check_if_price_changed_or_time_passed(stocks):
    data = get_data_from_file(DATABASE)

    now = time.datetime.now()
    minutes_since_last_update = get_minutes_since_last_update(data, now)

    stock_prices_old_dic = get_old_stock_prices(data)

    stock_prices_changes_dic = {}
    for stock_name in STOCKS_LIST:
        stock_prices_changes_dic[stock_name] = get_change(stock_prices_old_dic[stock_name], stocks[stock_name])

    new_data = prepare_data(stocks, stock_prices_changes_dic, stock_prices_old_dic, now)

    # always print stocks in log
    print("{} $$".format(time.datetime.now()))
    pp = pprint.PrettyPrinter()
    pp.pprint(new_data)

    important = is_change_important(new_data)

    print("Important: {}".format(important))
    if (PRE_MARKET_START <= now <= REGULAR_MARKET_END and (
            minutes_since_last_update >= UPDATE_PERIOD or minutes_since_last_update == -1)) or important:
        new_data = persist_market_price(new_data)
        return new_data

    return {}


def is_change_important(data):
    important = False
    data = data[STOCKS_KEY]

    for stock_names in STOCKS_LIST:
        stock_change = data[stock_names][CHANGE_SINCE_LAST_UPDATE_KEY]
        stock_change = math.sqrt(math.pow(stock_change, 2))

        important = stock_change >= IMPORTANT_CHANGE_THRESHOLD
        if important:
            return important

    return important


def prepare_data(stocks, stock_prices_changes_dic, stock_prices_old_dic, now):
    new_data = DATABASE_TEMPLATE
    new_data_stocks = new_data[STOCKS_KEY]

    for stock_name in STOCKS_LIST:
        if stock_name not in new_data_stocks:
            new_data_stocks[stock_name] = {}

        new_data_stocks[stock_name][MARKET_PRICE_KEY] = stocks[stock_name]
        new_data_stocks[stock_name][MARKET_PRICE_OLD_KEY] = stock_prices_old_dic[stock_name]
        new_data_stocks[stock_name][CHANGE_SINCE_LAST_UPDATE_KEY] = stock_prices_changes_dic[stock_name]

    new_data[LAST_UPDATE_KEY] = str(now)

    return new_data


def get_minutes_since_last_update(data, now):
    if data[LAST_UPDATE_KEY] != "":
        then = time.datetime.strptime(data[LAST_UPDATE_KEY], '%Y-%m-%d %H:%M:%S.%f')
        time_delta = now - then
        minutes_since_last_update = time_delta.total_seconds() / 60
        return minutes_since_last_update
    else:
        return -1


def get_data_from_file(file_name):
    try:
        with open(file_name, "r") as file:
            try:
                data = json.load(file)
            except JSONDecodeError:
                data = DATABASE_TEMPLATE

    except FileNotFoundError:
        print("test")
        open(file_name, "w+")
        data = DATABASE_TEMPLATE

    return data


def get_old_stock_prices(stock_data):
    stock_prices_old_dic = {}
    stocks = stock_data[STOCKS_KEY]

    for stock_name in STOCKS_LIST:
        if stock_name in stocks:
            stock_price_old = stocks[stock_name][MARKET_PRICE_KEY]
            stock_prices_old_dic[stock_name] = stock_price_old
        else:
            stock_prices_old_dic[stock_name] = 0

    return stock_prices_old_dic


def get_change(old, new):
    if old == 0:
        return 0

    change_value = new - old
    one_old = old / 100
    change = change_value / one_old

    return round(change, 2)


def compose_message(sender_mail, receiver_mail, stocks_data):
    message = MIMEMultipart("alternative")

    important = is_change_important(stocks_data)

    pre_subject = ""
    if important:
        pre_subject = PRE_SUBJECT_TEMPLATE.format(IMPORTANT_CHANGE_THRESHOLD)

    formatted_subject = create_subject(stocks_data)

    message["Subject"] = pre_subject + formatted_subject
    message["From"] = sender_mail
    message["To"] = ','.join(receiver_mail)

    # TODO order content
    content = MESSAGE_GREETING + build_content(stocks_data) + MESSAGE_CLOSING
    content_of_message = MIMEText(content, "plain")
    message.attach(content_of_message)

    return message


def create_subject(stocks_data):
    stocks = stocks_data[STOCKS_KEY]
    changes_absolute_dict = {}

    # TODO refactor
    for stock_name in stocks:
        change_neutral = stocks[stock_name][CHANGE_SINCE_LAST_UPDATE_KEY]
        change_neutral = math.sqrt(math.pow(change_neutral, 2))

        changes_absolute_dict[stock_name] = change_neutral

    ordered_changes_absolute_list = sorted(changes_absolute_dict.items(), key=operator.itemgetter(1), reverse=True)

    subject = ""
    for index, change in enumerate(ordered_changes_absolute_list[0:SUBJECT_STOCK_LIMITS], start=0):
        stock_key = change[0]
        selected_stock = stocks[stock_key]
        subject_delimiter = " / " if index > 0 else ""

        subject += subject_delimiter + SUBJECT_TEMPLATE.format(stock_name=stock_key,
                                                               stock_price=selected_stock[MARKET_PRICE_KEY],
                                                               stock_change=selected_stock[
                                                                   CHANGE_SINCE_LAST_UPDATE_KEY])
    return subject


def build_content(stocks_data):
    message = ""

    for index, stock_name in enumerate(STOCKS_LIST, start=0):
        stock_data = stocks_data[STOCKS_KEY][stock_name]

        dollar = stock_data[MARKET_PRICE_KEY]
        market_price_old = stock_data[MARKET_PRICE_OLD_KEY]
        change_since_last_update = stock_data[CHANGE_SINCE_LAST_UPDATE_KEY]

        message_delimiter = "\n" if index > 0 else ""
        message += message_delimiter + MESSAGE_CONTENT_TEMPLATE.format(stock_name=stock_name, dollar=dollar,
                                                                       old_dollar=market_price_old,
                                                                       euro=calc_eur_from_doll(dollar),
                                                                       old_euro=calc_eur_from_doll(market_price_old),
                                                                       stock_change=change_since_last_update)
    return message


# TODO currency conversion from old script and look in metadata from which currency you are converting
def calc_eur_from_doll(dollar_value):
    request_url = FREE_CURRENCY_URL.format(FREE_CURRENCY_API_KEY, CONVERSION_FROM_TO)

    response = requests.get(request_url)
    conversion = response.json()[CONVERSION_FROM_TO]
    euro_value = dollar_value * conversion
    return round(euro_value, 3)


def send_mail(sender, password, receivers, message):
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, PORT, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receivers, message.as_string())


if __name__ == '__main__':
    mapped_stocks = get_current_market_price()

    stocks_database_with_new_stocks = check_if_price_changed_or_time_passed(mapped_stocks)

    if stocks_database_with_new_stocks:
        msg = compose_message(SENDER_EMAIL, LIST_OF_E_MAILS, stocks_data=stocks_database_with_new_stocks)
        send_mail(SENDER_EMAIL, PASSWORD, LIST_OF_E_MAILS, msg)

        for receiver in LIST_OF_E_MAILS:
            print("{} $$ informed ".format(time.datetime.now()) + receiver + " by mail")
    else:
        print("{} $$ no mail is sent".format(time.datetime.now()))

    print(DELIMITER)
