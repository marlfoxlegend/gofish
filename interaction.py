from collections import deque
from itertools import starmap
from string import Formatter, ascii_letters, digits
from time import sleep
from typing import Optional, Sequence, Any, Union, Tuple

from gofish.card import Card, GOFISH_MAX_PLAYERS
from gofish.player import HumanPlayer, AiPlayer
from gofish.turn import Turn


class _GameStrings:
    WELCOME = 'GO FISH\nThe Go Fish card game in python. Created by Sean Cleveland.\n'
    ASK_CARD = '\n{turn.active} asks {turn.opponent} for a {turn.wanted_card}.'
    HAVE_CARD = '\n{turn.opponent}, do you have a {turn.wanted_card!s} ? (y/n)\nGOF >>> '
    RESPOND_POS = '\n{turn.opponent} HAS a {turn.wanted_card}! ' \
                  '{turn.active} takes it and goes again.'
    RESPOND_NEG = '\n{turn.opponent} HAS NO {turn.wanted_card}!'
    GO_FISHING = '\nGo Fish {turn.active}!'
    FISH_MATCH = '\n{turn.active} has drawn a matching card and gets another turn!'
    FISH_OTHER = '\n{turn.active} has drawn a matching card but ends turn.'
    FISH_NONE = '\n{turn.active} found no matches.'
    USER_GO_FISH = '\nYou drew a {turn.go_fish_card}'
    GAME_OVER = '\n!!! Game Over !!!'
    USER_LOSES = '\nBetter luck next time {0}!'
    USER_WINS = '\nCongratulations {0}, you won!'
    RANKINGS_HEADER = f'{chr(42) * 20} Player Rankings {chr(42) * 20}'
    PLAYERS_RANKED = '{0}\t{1:<10}'
    PLAYED_WON_LOSS = 'Played:\t{0.games_played:<{offset}}\n' \
                      'Wins:\t{1[win]:<{offset}}\nLosses:\t{1[loss]:<{offset}}'
    GET_NUM_AI = f'Enter the number of AI players to play against. ' \
                 f'(1-{GOFISH_MAX_PLAYERS})\nGOF >>> '
    GET_NAME = 'Please enter your name\nGOF >>> '
    GET_CARD_CHOICE = 'Enter the number below the card you want to match.\nGOF >>> '
    GET_OPP_CHOICE = 'Enter the number next to the player you want to ask.\nGOF >>> '
    WRONG_NUM_AI = f'Enter only numbers between 1-{GOFISH_MAX_PLAYERS}, inclusive.'
    WRONG_INDEX = 'Enter only the numbers shown.'
    WRONG_TYPE_NUM = 'Enter a number only.'
    WRONG_STRING = 'Alphanumeric characters only, please.'
    PLAY_AGAIN = 'Would you like to play again? (y/n)\nGOF >>> '
    WRONG_YESNO = 'Enter "y" or "n" only.'
    STOP_CHEATING = 'Stop trying to cheat!'


class GameStrings(Formatter, _GameStrings):
    def __init__(self, format_string: Optional[str] = None):
        super().__init__()
        self._format_string = format_string
        self._parsed_string = self.parse(self._format_string) if format_string else None

    def parse(self, format_string):
        return super().parse(format_string)

    def format_game_string(self, game_str: Optional[str] = None, *args, **kwargs):
        if not (self._format_string or game_str):
            raise ValueError('No string available to format.')
        if game_str:
            self._format_string = game_str
            self._parsed_string = self.parse(self._format_string)
        for littext, fldname, spec, conv in self._parsed_string:
            if fldname == 'turn':
                try:
                    val = self.get_value(fldname, args, kwargs)
                except (IndexError, KeyError):
                    print('No Turn found in kwargs despite "turn" being a field.')
                    raise
                return self._format_string.format(turn=val, *args, **kwargs)
        ret_str = self.format()
        return ret_str

    def new_format_string(self, nfs):
        if isinstance(nfs, str):
            self._format_string = nfs
            self._parsed_string = self.parse(self._format_string)


# game_strings = GameStrings()


class MessageQueue:
    def __init__(self):
        self.messages = deque()

    def add_message(self, msg: Union[str, GameStrings], *args, urgent=False, **kwargs):
        _msg = msg.format(*args, **kwargs)
        self.messages.append((urgent, _msg))

    def extend_queue(self, *args: Tuple[Any]):
        if args:
            starmap(self.add_message, args)

    def execute(self):
        while self.messages:
            urgent, message = self.messages.popleft()
            print(message)
            if not urgent:
                sleep(3)


class GamePrompts:
    def __init__(self):
        self.game_strings = GameStrings()

    def have_card(self, turn: Turn, matched: bool):
        if turn.opponent.is_human:
            lying = True
            while lying:
                answer = input(self.game_strings.
                               format_game_string(self.game_strings.HAVE_CARD, turn))
                lying = (answer == 'y' and not matched) or (answer == 'n' and matched)
                if not lying:
                    break
                print(self.game_strings.STOP_CHEATING)

    def num_ai_prompt(self) -> int:
        """Get user input for number of AI players to play against."""
        while True:
            answer = input(self.game_strings.GET_NUM_AI)
            if answer in digits:
                if 1 <= int(answer) <= GOFISH_MAX_PLAYERS:
                    return int(answer)
                print(self.game_strings.WRONG_NUM_AI)
                continue
            print(self.game_strings.WRONG_TYPE_NUM)

    def choose_opp_prompt(self, others: Sequence[AiPlayer]) -> AiPlayer:
        """Validate user input to select an opponent for this turn."""

        while True:
            answer = input(self.game_strings.GET_OPP_CHOICE)
            if answer in digits:
                try:
                    # Check input is within index limits
                    return others[int(answer) - 1]
                except IndexError:
                    print(self.game_strings.WRONG_INDEX)
                    continue
            print(self.game_strings.WRONG_TYPE_NUM)

    def choose_card_prompt(self, user: HumanPlayer) -> Card:
        """
        Validate user input to select the index of the card to play.
        """
        print(*user.hand, sep='\t')
        print([f'{i:>4}' for i in range(user.hand.count())], sep='\t')
        while True:
            answer = input(self.game_strings.GET_CARD_CHOICE)
            # Validate input within index limit
            if answer in digits:
                try:
                    return user.hand.stack[int(answer) - 1]
                except IndexError:
                    print(self.game_strings.WRONG_INDEX)
                    continue
            print(self.game_strings.WRONG_TYPE_NUM)

    def get_name_prompt(self):
        while True:
            answer = input(self.game_strings.GET_NAME)
            if all(s in ascii_letters for s in answer):
                return answer
            print(self.game_strings.WRONG_STRING)

    def play_again(self):
        answer = input(self.game_strings.PLAY_AGAIN)
        if answer.isalpha():
            return answer[0].lower() == 'y'
        print(self.game_strings.WRONG_YESNO)
