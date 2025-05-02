#!/usr/bin/env python3

# Fetches consumption data from https://mieter.techem.de/ programmatically

import time
import argparse
import json
import msal
import webbrowser
from urllib import parse
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

import logging

AUTHORITY = "https://techemtenantportal.b2clogin.com/techemtenantportal.onmicrosoft.com/b2c_1a_signin"
API_BASE = "https://mieter.techem.de/api/v1"
CLIENT_ID = "e2c8cff8-17bc-41c7-89b6-5bee13c7f556"
SCOPES = [
    "https://techemtenantportal.onmicrosoft.com/eedo-be-consumption-service/access_as_user",
]
REDIRECT_URI = "https://mieter.techem.de/auth"

LOG_LEVEL = logging.INFO


def main():
    log = logging.getLogger(__name__)
    log.setLevel(LOG_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    log.addHandler(ch)

    parser = argparse.ArgumentParser(
        prog="techem.py",
        description="Scrapes consumption data (Verbrauchsinfo) from Techem website",
    )
    parser.add_argument("-B", "--browser", action="store_true")
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()
    get_eed(args, log)


def get_eed(args, log):
    result = login(args, log)

    rental_agreements = str.split(result["id_token_claims"]["rentalAgreements"][0], ";")
    unit_id = rental_agreements[0]
    party_id = rental_agreements[1]
    base_url = f"{API_BASE}/consumptions/residential-units/{unit_id}/consumptions"
    access_token = result["access_token"]
    # python requests' UA gets blocked, so pretend to be Chrome
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
    }

    # Fetch consumption periods
    # https://mieter.techem.de/api/v1/consumptions/residential-units/UNIT_ID/consumptions/periods?limit=XX
    periods_url = f"{base_url}/periods?limit=100"
    periods = fetch_data(periods_url, "periods.json", headers, log)

    data = periods.json()["data"]
    log.info("Fetching consumption data")
    for p in data:
        period = p["period"]

        # Fetch consumption data for this period
        # https://mieter.techem.de/api/v1/consumptions/residential-units/UNIT_ID/consumptions/YYYY-MM
        consumption_url = f"{base_url}/{period}"
        fetch_data(consumption_url, f"{period}.json", headers, log)

        # Fetch average data for this period (comparable to appartments similarly sized)
        # https://mieter.techem.de/api/v1/consumptions/statistics/residential-units/UNIT_ID/consumptions/YYYY-MM/average
        consumption_average_url = f"{API_BASE}/consumptions/statistics/residential-units/{unit_id}/consumptions/{period}/average"
        fetch_data(consumption_average_url, f"{period}-average.json", headers, log)


def login(args, log):
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID, authority=AUTHORITY, client_credential=None
    )
    flow = app.initiate_auth_code_flow(scopes=SCOPES, redirect_uri=REDIRECT_URI)
    if "error" in flow:
        raise ValueError(flow.get("error"))
    auth_url = flow["auth_uri"]
    if args.browser:
        log.info(f"Go to this URL to login: {auth_url}")
        log.info(
            "A browser window should open automatically, if not enter the URL above"
        )
        webbrowser.open(auth_url, new=0, autoraise=True)
        auth_response_url = input("Enter resulting redirect_url: ").rstrip("\n")
    else:
        log.info("Automated login")
        auth_response_url = login_with_selenium(args, auth_url, log)
    if not auth_response_url.startswith("https://mieter.techem.de/auth?state="):
        raise Exception(
            "Wrong URL, needs to start with https://mieter.techem.de/auth?state="
        )
    auth_response = dict(parse.parse_qsl(parse.urlsplit(auth_response_url).query))
    result = app.acquire_token_by_auth_code_flow(flow, auth_response)
    log.info("Auth successful")
    log.debug(f"Auth Result:\n {result}")
    return result


def login_with_selenium(args, auth_url, log):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.get(auth_url)
    driver.implicitly_wait(2)
    username_box = driver.find_element(by=By.ID, value="signInName")
    username_box.send_keys(args.username)
    password_box = driver.find_element(by=By.ID, value="password")
    password_box.send_keys(args.password)
    submit_button = driver.find_element(by=By.ID, value="next")
    submit_button.click()
    time.sleep(4)
    return driver.current_url


def fetch_data(url, filename, headers, log):
    log.debug(f"Fetching data from: {url}")
    data = requests.get(url, headers=headers)
    with open(filename, "w") as f:
        json.dump(data.json(), f, ensure_ascii=False, indent=4)
    log.debug(f"Response body:\n{data.text}")
    return data


if __name__ == "__main__":
    main()
