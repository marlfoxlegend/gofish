import collections as coll
import enum
import itertools as itt
import random
import types
import typing as tp
from gofish.interaction import GamePrompts, GameStrings
from gofish.card import Card
from gofish.player import AnyPlayer

prompt_ = GamePrompts()


class TurnOutcomes(enum.Enum):
    IN_PROGRESS = enum.auto()
    ASKED_MATCH = enum.auto()
    FISH_MATCH = enum.auto()
    FISH_OTHER = enum.auto()
    FISH_NONE = enum.auto()

    def extra_turns(self) -> int:
        """Returns the integer to rotate the deque of players."""
        return 0 if self in [self.ASKED_MATCH, self.FISH_MATCH] else -1


def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def user_choose_card(turn: 'Turn'):
    turn.active.view_hand()
    turn.wanted_card = prompt_.choose_card_prompt(turn.active)
    return turn


def user_choose_opp(turn: 'Turn'):
    print(*[f'{n}) {p!s}' for n, p in enumerate(turn.game.players[1:], start=1)], sep='\n')
    turn.opponent = prompt_.choose_opp_prompt(turn.game.players[1:])


def ai_choose_card(turn: 'Turn'):
    """
    Test for remembered cards weighted towards user's picks

    Iterate over AI instance attribute's ``opp_choices`` if a user key exists
    filter the set of cards to a tuple of matching
    indexes in the AI instance attribute's ``hand``. If the tuple is empty
    choose any card.
    """

    sorted_opp = dict(sorted(turn.active.opp_choices.items(), key=lambda x: x[0]._sort_order))
    for opp, cards in sorted_opp.items():
        # Since the set of remembered cards is not empty
        # filtering out the None's will keep all matching indexes
        matches = [
            *itt.filterfalse(lambda x: x is None, map(turn.active.hand.has_match, cards))]
        if matches:
            # Set turn state values and return
            turn.opponent = opp
            turn.wanted_card = turn.active.hand.stack[matches.pop()]
            return turn
    if not turn.wanted_card:
        turn.wanted_card = random.choice(turn.active.hand.stack)
    return turn


def ai_choose_opp(turn: 'Turn'):
    if not turn.opponent:
        turn.opponent = random.choice(turn.game.turn_order)


Turns = coll.namedtuple('Turns', 'user ai')
gofish_turns = Turns({'card': user_choose_card, 'opp': user_choose_opp},
                     {'card': ai_choose_card, 'opp': ai_choose_opp})


class Turn:
    def __init__(self, game, card_strat=user_choose_card, opp_strat=user_choose_opp):
        self.game = game
        self.active = game.turn_order.popleft()
        self.outcome = TurnOutcomes.IN_PROGRESS
        self.card_strat = types.MethodType(card_strat, self)
        self.opp_strat = types.MethodType(opp_strat, self)
        self.opponent: tp.Optional[AnyPlayer] = None
        self.wanted_card: tp.Optional[Card] = None
        self.matching_card: tp.Optional[Card] = None
        self.go_fish_card: tp.Optional[Card] = None

    def print_stats(self):
        print(f'Deck: {len(self.game.deck)}')
        # print('{:>10}\t{:>5}\t{:^5}'.format(*'Player Cards Score'.split()))
        stat = '{0.name:>10}(Cards: {0.hand.count:<} Pairs: {0.num_pairs:<})'
        print(*[stat.format(p.name) for p in self.game.players], sep=' ')
        print(self.game.user)

    def enter(self):
        clear_screen()
        self.outcome = TurnOutcomes.IN_PROGRESS
        self.print_stats()
        print(self.active.title)
        self.card_strat().opp_strat()
        return self

    def exit(self):
        self.game.messages.execute()
        self.active.collect_pairs()

    def execute(self):
        self.enter().do_ask()
        if self.outcome is TurnOutcomes.IN_PROGRESS:
            self.do_go_fish()
        self.exit()

    def do_ask(self, outcomes=TurnOutcomes):
        """Check opponent's hand for a match to wanted card."""

        self.game.messages.add_message(self.game.strings.ASK_CARD, turn=self)
        match = self.opponent.hand.has_match(self.wanted_card)
        if match is not None:
            self.outcome = outcomes.ASKED_MATCH
            self.game.messages.add_message(self.game.strings.RESPOND_POS, turn=self)
            self.active.hand.add_to_hand(self.opponent.hand.pop_card(match))
        else:
            self.game.messages.add_message(self.game.strings.RESPOND_NEG, turn=self)

    def do_go_fish(self, outcomes=TurnOutcomes):
        """Player draws from the deck and checks for matches

        Player draws from deck and checks if the drawn card matches wanted card,
        failing that, check if card matches any card in hand.
        """

        self.go_fish_card = self.game.deck.take_top()
        if self.wanted_card.same_rank(self.go_fish_card):
            # if not self.opponent.is_human:
            #     self.opponent.forget(self.active, self.wanted_card)
            self.outcome = outcomes.FISH_MATCH
            self.game.messages.add_message(self.game.strings.FISH_MATCH, turn=self)
        else:
            if not self.opponent.is_human:
                self.opponent.remember(self.active, self.wanted_card)
            matches = self.active.hand.has_match(self.go_fish_card)
            if matches is not None:
                self.matching_card = self.active.hand.pop_card(matches)
                self.outcome = outcomes.FISH_OTHER
                self.game.messages.add_message(self.game.strings.FISH_OTHER, turn=self)
            else:
                self.outcome = outcomes.FISH_NONE
                self.game.messages.add_message(self.game.strings.FISH_NONE, turn=self)
        self.active.hand.add_to_hand(*[c for c in [self.go_fish_card, self.matching_card] if c])


class AiTurn(Turn):
    def __init__(self, game):
        super().__init__(game, ai_choose_card, ai_choose_opp)

    def do_ask(self, outcomes=TurnOutcomes):
        self.outcome = outcomes.IN_PROGRESS
        self.game.messages.add_message(self.game.strings.ASK_CARD, turn=self)
        match = self.opponent.hand.has_match(self.wanted_card)
        self.game.prompts.have_card(self, False if match is None else True)
        if match is not None:
            self.outcome = outcomes.ASKED_MATCH
            self.game.messages.add_message(self.game.strings.RESPOND_POS, turn=self)
            self.active.hand.add_to_hand(self.opponent.hand.pop_card(match))
        else:
            self.game.messages.add_message(self.game.strings.RESPOND_NEG, turn=self)
