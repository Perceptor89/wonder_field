from dotenv import load_dotenv
import requests
import os
import logging


load_dotenv()


def send_request(method: str, params: dict):
    logging.info(f'Params to send: {params}')
    token = os.getenv('BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/{method}"

    with requests.session() as session:
        with session.get(url, json=params) as resp:
            logging.info(resp.json())
            return resp.json()
