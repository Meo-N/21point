"""控制台二十一点（Blackjack）游戏。"""

import random

SUITS = ("♠", "♥", "♣", "♦")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

from dataclasses import dataclass

@dataclass
class Card:
    suit: str
    rank: str

    def get_value(self):
        if self.rank == "A":
            return 11
        elif self.rank in ["J", "Q", "K"]:
            return 10
        else:
            return int(self.rank)

    def __str__(self):
        return self.suit + self.rank


class Deck:
    # 一副洗好的标准 52 张扑克牌

    def __init__(self, rng=None):
        self._cards = []

        # 创建52张牌
        for suit in SUITS:
            for rank in RANKS:
                card = Card(suit, rank)
                self._cards.append(card)

        # 洗牌
        if rng is None:
            random.shuffle(self._cards)
        else:
            rng.shuffle(self._cards)

    def deal(self):
        if not self._cards:
            raise RuntimeError("牌堆中已经没有牌了")
        return self._cards.pop()


def hand_value(hand):
    # 计算手牌最优点数（可自动将A从11点改计为1点）
    total = sum(card.get_value() for card in hand)
    aces = sum(card.rank == "A" for card in hand)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def format_hand(hand):
    return "  ".join(str(card) for card in hand)


def ask_choice(prompt, choices):

    while True:
        answer = input(prompt).strip().lower()
        for canonical, aliases in choices.items():
            if answer in aliases:
                return canonical
        print("输入无效，请重新选择。")


def show_table(player, dealer, hide_dealer):
    print("\n" + "─" * 34)
    if hide_dealer:
        print(f"庄家：{dealer[0]}  [暗牌]")
    else:
        print(f"庄家：{format_hand(dealer)}  （{hand_value(dealer)} 点）")
    print(f"玩家：{format_hand(player)}  （{hand_value(player)} 点）")
    print("─" * 34)


def determine_result(player, dealer):
    player_total = hand_value(player)
    dealer_total = hand_value(dealer)
    if player_total > 21:
        return "loss"
    if dealer_total > 21 or player_total > dealer_total:
        return "win"
    if player_total < dealer_total:
        return "loss"
    return "draw"


def play_round():
    """进行一局游戏并返回 win、loss 或 draw。"""

    deck = Deck()
    player = []
    dealer = []

    # 交替发牌
    for _ in range(2):
        player.append(deck.deal())
        dealer.append(deck.deal())

    show_table(player, dealer, hide_dealer=True)

    # 玩家阶段（初始 21 点无需再操作）
    while hand_value(player) < 21:
        action = ask_choice(
            "请选择：[H] 要牌（Hit） / [S] 停牌（Stand）：",
            {"hit": {"h", "hit", "要牌"}, "stand": {"s", "stand", "停牌"}},
        )
        if action == "stand":
            break
        new_card = deck.deal()
        player.append(new_card)
        print(f"\n你抽到了：{new_card}")
        show_table(player, dealer, hide_dealer=True)

    if hand_value(player) > 21:
        print("你爆牌了！")
        show_table(player, dealer, hide_dealer=False)
        return "loss"

    print("\n庄家翻开暗牌。")
    show_table(player, dealer, hide_dealer=False)

    # 规则要求庄家必须要牌直到点数达到 17。
    while hand_value(dealer) < 17:
        new_card = deck.deal()
        dealer.append(new_card)
        print(f"庄家抽到了：{new_card}")
        show_table(player, dealer, hide_dealer=False)

    return determine_result(player, dealer)


def main():

    scores = {"win": 0, "loss": 0, "draw": 0}
    messages = {
        "win": "恭喜，你赢了！",
        "loss": "庄家获胜。",
        "draw": "本局平局。",
    }

    print("═" * 34)
    print("       欢迎来到二十一点 Blackjack")
    print("═" * 34)

    while True:
        result = play_round()
        scores[result] += 1
        print(f"\n{messages[result]}")
        print(
            f"当前战绩：胜 {scores['win']}  |  "
            f"负 {scores['loss']}  |  平 {scores['draw']}"
        )

        again = ask_choice(
            "\n是否继续？[Y] 继续 / [N] 退出：",
            {"yes": {"y", "yes", "是", "继续"}, "no": {"n", "no", "否", "退出"}},
        )
        if again == "no":
            print("感谢游玩，再见！")
            break
        print("\n开始新的一局……")


if __name__ == "__main__":
    main()
