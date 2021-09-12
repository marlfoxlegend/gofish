import collections as coll
import itertools as itt
import operator as oper
import random
import typing as tp

from gofish.card import Deck
from gofish.interaction import MessageQueue, GamePrompts, GameStrings
from gofish.player import HumanPlayer, AiPlayer, AnyPlayer
from gofish.turn import Turn, AiTurn, clear_screen

prompts_ = GamePrompts()


def create_human_player() -> HumanPlayer:
    name = prompts_.get_name_prompt()
    return HumanPlayer(name.upper())


def create_ai_player(num_ai: int = 1) -> tp.Tuple[AiPlayer, ...]:
    return tuple(map(AiPlayer, range(1, num_ai + 1)))  # return tuple(repeatfunc(AiPlayer, num_ai))


def new_deck(d: tp.Optional[Deck] = None) -> Deck:
    if not d:
        d = Deck()
    d.reset()
    return d


def randomize_turns(players: tp.Sequence[AnyPlayer]) -> tp.Deque[AnyPlayer]:
    _players = list(players)
    random.shuffle(_players)
    return coll.deque(_players)


def build_players(same_user=None) -> tp.Tuple[AnyPlayer, ...]:
    """
    Build all players for the game.

    :parameter same_user: a user instance to use instead of creating a new one.
    :type same_user: player.HumanPlayer | None
    """
    if same_user is None:
        same_user = create_human_player()
    num_ai = prompts_.num_ai_prompt()
    return same_user, *create_ai_player(num_ai)


def filtfalse_players(players: tp.Sequence[AnyPlayer], pred: tp.Callable[[AnyPlayer], bool]):
    return tuple(itt.filterfalse(pred, players))


class GoFish:
    strings = GameStrings()
    prompts = GamePrompts()
    messages = MessageQueue()
    winloss = {'win': 0, 'loss': 0}
    games_played = 0

    def __init__(self):
        print(self.strings.WELCOME)
        self.deck = new_deck()
        self.user = create_human_player()
        self.players: tp.Sequence[AnyPlayer] = build_players(self.user)
        self.turn_order = randomize_turns(self.players)

    def new_game(self, first=False):
        """Start a new game by (re)initializing required variables."""

        if not first:
            clear_screen()
            self.user.hand.clear_hand()
            self.deck = new_deck()
            self.players = build_players(self.user)
            self.turn_order = randomize_turns(self.players)
        self.deck.deal_hands(*map(oper.attrgetter('hand'), self.players))
        for p in self.players:
            p.collect_pairs()

    def game_over(self):
        """Game is over when the deck or any player's hand reaches 0."""

        finished = (len(self.deck) == 0) or any(p.hand.count == 0 for p in self.players)
        if finished:
            self.messages.add_message(self.strings.GAME_OVER)
        return finished

    def score_game(self):
        """Sort players by num_pairs and check if the user got 1st place."""

        ranked = sorted(self.players, key=lambda x: x.num_pairs, reverse=True)
        wl = 'win' if ranked[0] is self.user else 'loss'
        self.winloss[wl] += 1
        return ranked

    def print_scores(self, sorted_players: tp.List[AnyPlayer]):
        """Take ranked players and display their scores to the user."""

        # Collect all strings for prep before sending to the queue
        self.messages.add_message(self.strings.RANKINGS_HEADER)
        # Add each enumerated iteration of sorted players to the message queue
        for num, player in enumerate(sorted_players, start=1):
            self.messages.add_message(self.strings.PLAYERS_RANKED, num, player.name, urgent=True)
        # Dynamic display win or loss
        if sorted_players[0] is self.user:
            msg_user_wl = self.strings.USER_WINS
        else:
            msg_user_wl = self.strings.USER_LOSES
        self.messages.add_message(msg_user_wl, self.user, urgent=True)
        self.messages.add_message(self.strings.PLAYED_WON_LOSS, self, self.winloss, offset=8,
                                  urgent=True)
        self.messages.execute()

    def next_turn(self, turn: tp.Optional[tp.Union[Turn, AiTurn]] = None) -> tp.Union[Turn, AiTurn]:
        """
        Rotate player order depending on the active player's outcome.

        :param turn: The current Turn being used in the game.
        :return: A new Turn depending on the active player's type
        """
        if not turn:
            return Turn(self) if self.turn_order[0].is_human else AiTurn(self)
        rotation = turn.outcome.extra_turns()
        self.turn_order.appendleft(turn.active)
        self.turn_order.rotate(rotation)
        return Turn(self) if self.turn_order[0].is_human else AiTurn(self)

    def play(self):
        self.new_game(False if self.games_played else True)
        turn = self.next_turn()
        while not self.game_over():
            turn.execute()
            turn = self.next_turn(turn)
        self.games_played += 1
        self.print_scores(self.score_game())
