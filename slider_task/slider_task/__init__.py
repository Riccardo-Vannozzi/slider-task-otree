from otree.api import *
import time
import math


author = 'Riccardo Vannozzi'


doc = """
Slider Task
"""


class C(BaseConstants):
    NAME_IN_URL = 'slider_task'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 10  # Number of paid rounds
    TIME_FOR_TASK = 120  # Duration of each paid round, in seconds
    TIME_FOR_BREAK = 10  # Break duration between the rounds of the task, in seconds
    PIECE_RATE = 2  # Piece-rate payment, in cents


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    initial_zoom = models.FloatField()   # Device pixel ratio (DPR) at the beginning of the task
    current_zoom = models.FloatField()  # Updated DPR if the participant changes browser zoom
    uses_mobile = models.BooleanField(initial=False)  # True for participants using smartphones or tablets
    screen_height = models.FloatField(initial=0)   # Screen height in CSS pixels
    screen_width = models.FloatField(initial=0)  # Screen width in CSS pixels
    time_left = models.IntegerField()  # Time left to complete the current round, in seconds
    practice_score = models.IntegerField(initial=0)  # Score in the practice round
    score = models.IntegerField(initial=0)  # Score in each paid round


# Return remaining time in the current round
def get_timeout_seconds(player):
    participant = player.participant
    return participant.time_expiry - time.time()


class Welcome(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    # Store screen width and height and type of device used
    @staticmethod
    def live_method(player: Player, data):
        if data.get("information_type") == "is_mobile":
            player.uses_mobile = bool(data.get("is_mobile"))
        if data["information_type"] == "size":
            player.screen_width = data["screen_width"]
            player.screen_height = data["screen_height"]


# Filter out participants using tablet or smartphone (optional)
class DropMobile(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and player.uses_mobile is True


# Initialize timer for practice round
class BeforePractice(Page):
    @staticmethod
    def before_next_page(player, timeout_happened):
        participant = player.participant
        participant.time_expiry = time.time() + C.TIME_FOR_TASK

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class PracticeRound(Page):
    get_timeout_seconds = get_timeout_seconds

    @staticmethod
    def is_displayed(player):
        player.time_left = math.ceil(get_timeout_seconds(player))
        return player.round_number == 1 and get_timeout_seconds(player) > 0

    # Store practice score
    @staticmethod
    def live_method(player: Player, data):
        if data["information_type"] == "score":
            player.practice_score = data["score"]



# Initialize round timer
class BeforeRounds(Page):
    @staticmethod
    def before_next_page(player, timeout_happened):
        participant = player.participant
        participant.time_expiry = time.time() + C.TIME_FOR_TASK


class Slider(Page):
    get_timeout_seconds = get_timeout_seconds

    @staticmethod
    def vars_for_template(player):
        player.time_left = math.ceil(get_timeout_seconds(player))

    # Store score and zoom changes
    @staticmethod
    def live_method(player: Player, data):
        if data["information_type"] == "initial_zoom":
            player.initial_zoom = data["initial_zoom"]
        if data["information_type"] == "zoom":
            player.current_zoom = data["zoom"]
        if data["information_type"] == "score":
            player.score = data["score"]


# Break between paid rounds (optional)
class Break(Page):
    timeout_seconds = C.TIME_FOR_BREAK

    @staticmethod
    def is_displayed(player):
        return player.round_number < C.NUM_ROUNDS


class StudyComplete(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        player.participant.tot_score = sum(player.in_round(i).score for i in range(1, C.NUM_ROUNDS + 1))
        player.participant.tot_payment = cu(
            player.participant.tot_score * C.PIECE_RATE / 100
        )


page_sequence = [
    Welcome,
    DropMobile,  # Comment out to remove filter on participants using a mobile device
    BeforePractice,
    PracticeRound,
    BeforeRounds,
    Slider,
    Break,  # Comment out to remove break between paid rounds
    StudyComplete
]
