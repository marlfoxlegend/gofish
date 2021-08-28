from collections import defaultdict
from types import MethodType
from typing import Union

from gofish.card import Hand, Card

bound_method = MethodType


class Player:
    def __init__(self, name: str, is_human: bool):
        self._name = name
        self._is_human = is_human
        self.hand = Hand()
        self.pairs = []
        self._sort_order = None

    def __str__(self):
        return self._name

    def collect_pairs(self):
        self.pairs.extend(self.hand.extract_pairs())

    @property
    def num_cards(self):
        return len(self.hand)

    @property
    def num_pairs(self):
        return len(self.pairs)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def is_human(self):
        return self._is_human

    @property
    def title(self):
        flair = '=' * 10
        return f"{flair} {self.name}'s TURN {flair}"


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name, True)
        self._sort_order = 0.0
        self.hand = Hand()
        self.pairs = []

    def view_hand(self):
        print(*self.hand)


class AiPlayer(Player):
    def __init__(self, idnum: int):
        super().__init__(f'COMPUTER_{idnum}', False)
        self._sort_order = float(idnum)
        self.opp_choices = defaultdict(set)

    def remember(self, player: 'AnyPlayer', asked_card: Card):
        self.opp_choices[player].add(asked_card)

    def forget(self, player: 'AnyPlayer', asked_card: Card):
        self.opp_choices[player].discard(asked_card)


AnyPlayer = Union[HumanPlayer, AiPlayer]
