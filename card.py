import collections as coll
import enum
import itertools as itt
import random
import typing as tp

import gofish.recipes as recipes

GOFISH_HAND_SIZE = 7
GOFISH_MAX_PLAYERS = 5


def set_globals():
    global GOFISH_HAND_SIZE
    global GOFISH_MAX_PLAYERS


set_globals()


class Suit(enum.Enum):
    """Suit of the Card and corresponding symbol."""
    SPADE = 0x2660
    CLUB = 0x2663
    HEART = 0x2665
    DIAMOND = 0x2666

    def __repr__(self):
        return f'<Suit({self.value:#X}): {self.name}>'

    def __str__(self):
        return chr(self.value)


class Card:
    """Class representing a single playing card"""

    FACES = {
        11: 'J',
        12: 'Q',
        13: 'K',
        1: 'A'
    }

    def __init__(self, rank: int, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __repr__(self):
        return f'Card({self.rank}{self.suit!s})'

    def __str__(self):
        try:
            rank = self.FACES[self.rank]
        except KeyError:
            rank = self.rank
        return f'|{rank}{self.suit!s}|'

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __ge__(self, other):
        return self.rank >= other.rank

    def __gt__(self, other):
        return self.rank > other.rank

    def __le__(self, other):
        return self.rank <= other.rank

    def __lt__(self, other):
        return self.rank < other.rank

    # def to_string(self):
    #     if self.rank in self.FACES:
    #         return self.FACES[self.rank]
    #     else:
    #         return self.rank

    def same_rank(self, other):
        try:
            return self.rank == other.rank
        except AttributeError:
            return False

    def same_suit(self, other):
        try:
            return self.suit is other.suit
        except AttributeError:
            return False


class Hand:
    def __init__(self, cards: tp.Optional[tp.Sequence[Card]] = None):
        if cards is None:
            cards = []
        self.stack: tp.Deque[Card] = coll.deque(cards)

    def __repr__(self):
        return f'<Hand: {self.count} cards>'

    def __iter__(self):
        return iter(self.stack)

    def __len__(self):
        return len(self.stack)

    def sort(self):
        sorted_hand = sorted(self.stack)
        self.stack = coll.deque(sorted_hand)

    def extract_pairs(self):
        self.sort()
        grouped = [list(grp) for _, grp in itt.groupby(self.stack, key=lambda x: x.rank)]
        grouped = filter(lambda x: len(x) > 1, grouped)
        pairs = []
        for group in grouped:
            for pair in recipes.grouper(group, 2):
                pairs.append(tuple(self.take_from_hand(*pair)))
        return pairs
        # for c in self.stack:
        #     dups[c.rank].append(c)
        # for dup_rank in filter(lambda x: len(x) > 1, dups.values()):
        #     removed = self.take_from_hand(*dup_rank)
        #     yield recipes.pairwise(removed)

    def pop_card(self, n: int) -> Card:
        """Pop out card at index n."""
        self.stack.rotate(-n)
        obj = self.stack.popleft()
        self.stack.rotate(n)
        return obj

    def add_to_hand(self, *cards: Card):
        if cards:
            not_card = [*itt.filterfalse(lambda x: isinstance(x, Card), cards)]
            if not_card:
                raise TypeError('Non-Card object in parameter cards in Hand.__init__')
            self.stack.extend(cards)

    def has_match(self, other_card: Card):
        """Check if other card is in hand and, if so, return its index else None."""

        for c in self.stack:
            if c.same_rank(other_card):
                return self.stack.index(c)
        return None

    def take_from_hand(self, *cards: Card):
        taken = []
        for c in cards:
            try:
                taken.append(self.pop_card(self.stack.index(c)))
            except IndexError:
                continue
        return taken

    def clear_hand(self):
        self.stack.clear()

    def count(self) -> int:
        """Show remaining count of cards in hand."""
        return len(self.stack)


# noinspection PyShadowingNames
class Deck:
    """Class composed of Cards representing a card_stack of cards."""

    def __init__(self):
        self.stack = coll.deque(self.get_standard_deck())
        self.shuffle_deck()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f'<Deck: {len(self)}>'

    def __iter__(self):
        return next(self)

    def __next__(self):
        while self.stack:
            c = self.stack.popleft()
            yield c

    def __len__(self):
        return len(self.stack)

    def reset(self):
        d = self.__class__()
        self.stack.clear()
        self.stack.extend(d)

    @staticmethod
    def get_standard_deck():
        return list(itt.starmap(Card, itt.product(range(1, 14), Suit)))
        # return [Card(r, s) for r, s in itt.product(Rank.values(), Suit)]

    def shuffle_deck(self, cut: int = 26):
        """Shuffle cards in deck."""

        self.stack = coll.deque(random.sample(self.stack, k=len(self.stack)))
        self.stack.rotate(-cut)

    def take_top(self) -> Card:
        """Take top card from deck and return it."""

        try:
            return self.stack.popleft()
        except IndexError:
            pass

    def deal_hands(self, *hands: Hand):
        if not hands:
            raise RuntimeError('No Hand objects were given.')
        hand_size = GOFISH_HAND_SIZE
        num_hands = len(hands)
        total_dealt = hand_size * num_hands
        if total_dealt > len(self):
            toss = num_hands - GOFISH_MAX_PLAYERS
            print(f'Too many Hand objects given ({num_hands}). Removing {toss}')
            num_hands -= toss

        # _hands = list(Hand() for _ in range(num_hands))
        cycle_hands = itt.cycle(hands)
        for c in itt.islice(self, total_dealt):
            next(cycle_hands).add_to_hand(c)


# PlayingCards = tp.MutableSequence[Card]
# CardPair = tp.Tuple[Card, Card]
# CardPairs = tp.MutableSequence[CardPair]

if __name__ == '__main__':
    d = Deck()
    hands = list(recipes.repeatfunc(Hand, 4))
    d.deal_hands(*hands)
