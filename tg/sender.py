from dotenv import load_dotenv
import requests
import os
import logging


BOT_TOKEN=os.getenv('BOT_TOKEN')


def send_request(method: str, params: dict):
    logging.info(f'Params to send: {params}')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    with requests.session() as session:
        with session.get(url, json=params) as resp:
            logging.info(resp.json())
            return resp.json()
