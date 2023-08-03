from django_app import celery_app as app
from .game import dcs, logic, utils
from tg import send_request
import traceback
import os


HOST_ID = int(os.getenv('HOST_ID'))


@app.task(name='process_update')
def process_update(message: str):
    try:
        update = utils.update_to_class(message)
        if type(update) is dcs.MessageUpdate:
            if update.message.from_.id == HOST_ID:
                return
            logic.process_message_update(update.message)
        elif type(update) is dcs.CallbackUpdate:
            if update.callback_query.from_.id == HOST_ID:
                return
            logic.process_callback_update(update.callback_query)
    except Exception:
        trace = traceback.format_exc()
        send_report.delay(trace)


@app.task(name='short_reply')
def short_reply(chat_id: int, reply_to: int, text: str):
    logic.short_reply(chat_id, reply_to, text)


@app.task(name='send_report')
def send_report(report: str):
    request = {'chat_id': 900025436, 'text': report}
    send_request('sendMessage', request)
