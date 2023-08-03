from django.contrib import admin
from .models import TGUser, Game, Question, Score


@admin.register(TGUser)
class TGUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'tg_id', 'email', 'first_name',
                    'last_name', 'is_staff']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    fields = ['chat_id', 'question', 'game_state']
    list_display = ['chat_id', 'message_id', 'game_state', 'word_state',
                    'question', 'created_at']
    empty_value_display = '-empty-'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'word']
    list_display_links = ['word']
    ordering = ['word']
    list_per_page = 20


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ['game', 'player', 'earned_points', 'wheel_points',
                    'answer_type', 'is_active', 'is_turn']
    empty_value_display = '-empty-'
