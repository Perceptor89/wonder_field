from typing import Any
from django.core.management.base import BaseCommand, CommandParser
import os
from wonder_fields.models import Question


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file')
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> str | None:
        path = options['file']
        if not os.path.isfile(path):
            self.stdout.write('File does not exist')
            return

        with open(path, 'r') as file:
            data = file.readlines()

        if not data:
            self.stdout.write('No data in file')
            return
        elif len(data) % 2 != 0:
            self.stdout.write('Not even number of lines')
            return

        added_count = 0
        while data:
            desc = data.pop(0).strip()
            desc = desc if desc[-1] == '.' else f'{desc}.'
            word = data.pop(0).strip().upper()

            words = [q.word for q in Question.objects.only('word').all()]

            if word not in words:
                Question.objects.create(word=word, description=desc)
                added_count += 1

        self.stdout.write(f'Added {added_count} new words.')
