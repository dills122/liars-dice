from math import comb

from game.components.bets import Bet
from game.components.context import GameContext


class Shwimpevwild:
    name = "Shwimp"
    _c = 0.72
    _4 = 0.9
    _2 = -1.55
    _12 = 0.18
    _15 = 0.78
    _14 = -0.95
    _17 = 0.22
    _5 = 0.26
    _13 = 0.01
    _a = 0.08
    _18 = 0.36
    _1 = 0.1
    _3 = 0.006
    _19 = 0.055
    _7 = 0.34
    _9 = 0.18
    _6 = 0.66
    _8 = 0.78
    _e = 0.62
    _d = 0.8
    _f = 3.1
    _10 = 0.7
    _b = 0.24
    _1b = 0.04
    _1a = 0.008
    _11 = 0.14
    _16 = 0.035
    _1c = 1.0

    def __init__(self) -> None:
        self._2c = 0
        self._2b: tuple[int, int] | None = None
        self._32 = True
        self._23: bool | None = None
        self._30: dict[tuple[int, int, int], float] = {}

    def _2e(self, ctx: GameContext) -> None:
        for i in range(self._2c, len(ctx.bet_history)):
            entry = ctx.bet_history[i]
            bet = entry["bet"]
            key = (entry["game"], entry["round"])
            if key != self._2b:
                self._2b = key
                self._23 = bet.face == 1
                self._32 = bet.face != 1
            elif bet.face == 1:
                self._32 = False
        self._2c = len(ctx.bet_history)
        if ctx.prior_bet is None:
            self._32 = True
            self._23 = None

    def _2f(self, dice: int, need: int, p_num: int) -> float:
        if need <= 0:
            return 1.0
        if need > dice:
            return 0.0
        key = (dice, need, p_num)
        cached = self._30.get(key)
        if cached is not None:
            return cached
        p = p_num / 6
        value = sum((comb(dice, k) * p**k * (1 - p) ** (dice - k) for k in range(need, dice + 1)))
        self._30[key] = value
        return value

    def _26(self, face: int, wilds: bool) -> int:
        return 2 if wilds and face != 1 else 1

    def _2d(self, hand: list[int], face: int, wilds: bool) -> int:
        support = hand.count(face)
        if wilds and face != 1:
            support += hand.count(1)
        return support

    def _27(self, hand: list[int], quantity: int, face: int, total_dice: int, wilds: bool) -> float:
        own = self._2d(hand, face, wilds)
        unseen = total_dice - len(hand)
        return self._2f(unseen, quantity - own, self._26(face, wilds))

    def _28(self, quantity: int, face: int, total_dice: int, wilds: bool) -> float:
        return self._2f(total_dice, quantity, self._26(face, wilds))

    def _21(self, ctx: GameContext, face: int) -> float:
        biases = [row.get(face, 1 / 6) for row in ctx.stats.face_bias.values()]
        return sum(biases) / len(biases) if biases else 1 / 6

    def _22(self, ctx: GameContext) -> float:
        rates = list(ctx.stats.challenge_rate.values())
        average = sum(rates) / len(rates) if rates else 0.24
        try:
            idx = ctx.round_players.index(self.name)
        except ValueError:
            return average
        next_player = ctx.round_players[(idx + 1) % len(ctx.round_players)]
        return ctx.stats.challenge_rate.get(next_player, average)

    def _31(self, hand: list[int], quantity: int, face: int, total_dice: int, wilds: bool) -> float:
        if not wilds or face == 1:
            return 0.0
        own_ones = hand.count(1)
        if own_ones == 0:
            return 0.0
        wild_public = self._28(quantity, face, total_dice, True)
        plain_public = self._28(quantity, face, total_dice, False)
        return max(0.0, wild_public - plain_public) + own_ones * self._1b

    def _20(
        self, ctx: GameContext, quantity: int, face: int, total_dice: int, wilds: bool
    ) -> float:
        public_probability = self._28(quantity, face, total_dice, wilds)
        suspicion = 1.0 - public_probability
        base = self._22(ctx)
        return max(self._a, min(0.8, base + suspicion * self._18))

    def _25(self, ctx: GameContext) -> float:
        rates = list(ctx.stats.challenge_rate.values())
        average = sum(rates) / len(rates) if rates else 0.24
        if average > self._7:
            factor = self._6
        elif average < self._9 and len(ctx.round_players) >= 3:
            factor = self._8
        else:
            factor = self._c
        return max(self._e, min(self._d, factor))

    def _24(
        self, ctx: GameContext, hand: list[int], total_dice: int
    ) -> list[tuple[float, int, int]]:
        candidates = []
        unseen = total_dice - len(hand)
        factor = self._25(ctx)
        for face in range(2, 7):
            own = self._2d(hand, face, True)
            quantity = max(1, round(own + unseen * (2 / 6) * factor))
            probability = self._27(hand, quantity, face, total_dice, True)
            leverage = self._31(hand, quantity, face, total_dice, True)
            score = probability * self._f + own * self._10
            score += leverage * self._19
            score -= self._21(ctx, face) * self._b
            score -= quantity * self._13
            candidates.append((score, quantity, face))
        return candidates

    def _29(self, prior_bet: Bet, hand: list[int]) -> list[tuple[int, int]]:
        candidates = []
        own_on_bid_face = self._2d(hand, prior_bet.face, self._32)
        if own_on_bid_face > 0:
            candidates.append((prior_bet.quantity + 1, prior_bet.face))
        for face in range(prior_bet.face + 1, 7):
            if self._2d(hand, face, self._32) > 0:
                candidates.append((prior_bet.quantity, face))
        return candidates or [(prior_bet.quantity + 1, prior_bet.face)]

    def _1d(self, ctx: GameContext, prior_bet: Bet) -> float:
        overall = ctx.stats.bluff_rate.get(prior_bet.player)
        by_face = ctx.stats.bluff_rate_by_face.get(prior_bet.player, {}).get(prior_bet.face)
        if overall is not None and by_face is not None:
            return overall * 0.8 + by_face * 0.2
        if overall is not None:
            return overall
        return 0.5

    def _1e(self, ctx: GameContext, prior_bet: Bet, probability_true: float) -> float:
        value = (1.0 - probability_true) * self._4 + probability_true * self._2
        value += (self._1d(ctx, prior_bet) - 0.5) * self._1
        value += max(0.0, ctx.stats.current_round_velocity - 1.0) * self._3
        if not self._32 and prior_bet.face != 1:
            value += self._1a
        return value

    def _2a(
        self, ctx: GameContext, hand: list[int], quantity: int, face: int, total_dice: int
    ) -> float:
        wilds_after = self._32 and face != 1
        probability_true = self._27(hand, quantity, face, total_dice, wilds_after)
        challenge_rate = self._20(ctx, quantity, face, total_dice, wilds_after)
        support = self._2d(hand, face, wilds_after)
        challenged_ev = probability_true * self._15 + (1.0 - probability_true) * self._14
        pass_ev = self._12 + probability_true * self._11
        score = challenge_rate * challenged_ev + (1.0 - challenge_rate) * pass_ev
        score += support * self._17
        score += self._31(hand, quantity, face, total_dice, wilds_after) * self._16
        score -= self._21(ctx, face) * self._5
        score -= quantity * self._13
        if probability_true == 0.0:
            score -= self._1c
        return score

    def _1f(self, scored: list[tuple[float, int, int]]) -> tuple[int, int]:
        _, quantity, face = max(scored, key=lambda row: (row[0], -row[1], -row[2]))
        return (quantity, face)

    def algo(self, ctx: GameContext) -> Bet | None:
        self._2e(ctx)
        hand = ctx.hand
        if ctx.prior_bet is None:
            quantity, face = self._1f(self._24(ctx, hand, ctx.total_dice))
            return Bet(quantity, face, self.name)
        current_probability = self._27(
            hand, ctx.prior_bet.quantity, ctx.prior_bet.face, ctx.total_dice, self._32
        )
        call_ev = self._1e(ctx, ctx.prior_bet, current_probability)
        scored = [
            (self._2a(ctx, hand, quantity, face, ctx.total_dice), quantity, face)
            for quantity, face in self._29(ctx.prior_bet, hand)
        ]
        best_raise_ev = max((row[0] for row in scored))
        if call_ev > best_raise_ev:
            return None
        quantity, face = self._1f(scored)
        return Bet(quantity, face, self.name)
