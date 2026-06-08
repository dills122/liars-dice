import logging

logger = logging.getLogger(__name__)

FACES = list(range(1, 7))


class Bet:
    def __init__(self, quantity: int, face: int, player: str):
        """
        Args:
            quantity: Number of dice claimed to show `face`.
            face: Die face value (1-6). 1s are wild in non-1 bets.
            player: Name of the player placing the bet.
        """
        self.quantity = quantity
        self.face = face
        self.player = player

    def __str__(self):
        return f"{self.player}: {self.quantity}x{self.face}"


def bet_validator(prior_bet: Bet, current_bet: Bet) -> bool:
    """Returns True if current_bet is a legal raise over prior_bet.

    A legal raise must either:
    - Increase quantity (any face), or
    - Keep quantity the same and increase the face value.
    Face must be 1-6 and quantity must be >= 1.
    """
    if current_bet.face not in FACES or current_bet.quantity < 1:
        logger.error(f"Out-of-range bet: [{current_bet}]")
        return False
    if current_bet.quantity > prior_bet.quantity:
        return True
    if current_bet.quantity == prior_bet.quantity and current_bet.face > prior_bet.face:
        return True
    logger.error(f"Bid does not raise prior: [{prior_bet}] -> [{current_bet}]")
    return False


def bet_grader(hands: list, bet: Bet, wilds: bool = True) -> bool:
    """Returns True if the bet holds when all dice are revealed.

    Counts dice matching bet.face across all hands. When wilds=True, 1s also
    count toward any non-1 bet. wilds is set to False once someone bids on 1s
    in the current round.

    Args:
        hands: List of hands, where each hand is a list of int die values.
        bet: The bet being graded.
        wilds: Whether 1s count as wild for non-1 bets.
    """
    n = sum(hand.count(bet.face) for hand in hands)
    if wilds and bet.face != 1:
        n += sum(hand.count(1) for hand in hands)
    logger.info(f"Grading [{bet}] (wilds={'on' if wilds else 'off'}): found {n} matching dice")
    return n >= bet.quantity
