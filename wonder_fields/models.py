from django.db import models
from django.contrib.auth.models import AbstractUser


class TGUser(AbstractUser):
    tg_id = models.IntegerField(blank=False, unique=True, null=False)
    REQUIRED_FIELDS = ['tg_id']

    def __str__(self):
        return self.username


class Question(models.Model):
    word = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def save(self, *args, **kwargs) -> None:
        self.word = self.word.upper()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id} | {self.word}'


class Game(models.Model):
    state_choices = [
        ('R', 'registration'),
        ('G', 'guessing'),
        ('F', 'finished'),
    ]
    chat_id = models.IntegerField(blank=False, null=False)
    question = models.ForeignKey('Question', null=True,
                                 on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    game_state = models.CharField(choices=state_choices, default='R')
    word_state = models.CharField(max_length=50, blank=True)
    message_id = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)


class Score(models.Model):
    answer_types = [
        ('l', 'letter'),
        ('w', 'word'),
        ('n', 'no choice')
    ]
    player = models.ForeignKey('TGUser', on_delete=models.DO_NOTHING,
                               related_name='scores')
    game = models.ForeignKey('Game', on_delete=models.CASCADE,
                             related_name='scores')
    earned_points = models.IntegerField(default=0)
    wheel_points = models.IntegerField(default=0)
    answer_type = models.CharField(choices=answer_types, default='n')
    is_active = models.BooleanField(default=True)
    is_turn = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['player', 'game'],
                       name='unique_game_player')]
