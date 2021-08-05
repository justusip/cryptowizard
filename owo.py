import os
import re
import time
import sys
import typing

import requests
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("Fetching tickers...")
tickers = list(o["symbol"] for o in requests.get("https://api.binance.com/api/v3/exchangeInfo").json()["symbols"])
print(f"{len(tickers)} tickers loaded.")

username = 'bohod91247@nhmty.com'
password = 'svJTdYnYtm78jQh'
login_btn_xpath = "/html/body/div/div[2]/div/div/div/div/form/div/div/div[1]/div[2]/button[2]"
message_container_xpath = "/html/body/div/div[2]/div/div[2]/div/div/div/div[2]/div[2]/div[2]/main/div[1]/div/div/div"

channelURL = "https://discord.com/channels/811868305055940688/812679772852715551"
# channelURL = "https://discord.com/channels/863717564806332416/863717564806332419"

driver = webdriver.Firefox(executable_path=os.path.join(os.path.dirname(os.path.realpath(__file__)), "geckodriver"))
driver.get(channelURL)
WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))

# Initialize and input email
username_input = driver.find_element_by_name("email")
username_input.send_keys(username)

# Initialize and input password
password_input = driver.find_element_by_name("password")
password_input.send_keys(password)

# Initialize and login
login_button = driver.find_element_by_xpath(login_btn_xpath)
login_button.click()

WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, message_container_xpath)))

message_container = driver.find_element_by_xpath(message_container_xpath)
messages = message_container.find_elements_by_class_name("message-2qnXI6")


def ticker_detected(msg):
    if (match := re.search("#(.+)$", msg, re.MULTILINE)) is not None:
        ticker = match[1].upper() + "BTC"
        if ticker in tickers:
            return ticker
    if (match := re.search("^^([A-Za-z][A-Za-z][A-Za-z][A-Za-z]?[A-Za-z]?) is looking perfect", msg, re.MULTILINE)) is not None:
        ticker = match[1].upper() + "BTC"
        if ticker in tickers:
            return ticker
    return None


for message in messages:
    if (ticker := ticker_detected(message.text)) is not None:
        print(f"Detected {ticker} from past messages.")

while True:
    WebDriverWait(driver, 99999999).until(
        lambda x: len(message_container.find_elements_by_class_name("message-2qnXI6")) > len(messages))
    cur_messages = message_container.find_elements_by_class_name("message-2qnXI6")
    for cur_message in cur_messages:
        if cur_message not in messages:
            msg = cur_message.text
            if (ticker := ticker_detected(msg)) is not None:
                print(f"Detected {ticker}!")
            messages.append(cur_message)
