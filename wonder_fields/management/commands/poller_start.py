from typing import Any
from tg.poller import Poller
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        poller = Poller()
        try:
            poller.is_run = True
            poller.poll()
        except KeyboardInterrupt:
            poller.is_run = False
