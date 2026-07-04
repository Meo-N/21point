"""支持多人、下注和存档的控制台二十一点游戏。"""

import json
import os
import random
import sys
from dataclasses import dataclass


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SUITS = ("♠", "♥", "♣", "♦")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SAVE_FILE = os.path.join(os.path.dirname(__file__), "blackjack_save.json")


@dataclass
class Card:
    suit: str
    rank: str

    def get_value(self):
        if self.rank == "A":
            return 11
        if self.rank in ["J", "Q", "K"]:
            return 10
        return int(self.rank)

    def __str__(self):
        return self.suit + self.rank


class Deck:
    def __init__(self, card_stats):
        self._cards = []
        self.card_stats = card_stats

        for suit in SUITS:
            for rank in RANKS:
                self._cards.append(Card(suit, rank))

        random.shuffle(self._cards)

    def deal(self):
        if not self._cards:
            raise RuntimeError("牌堆中已经没有牌了")

        card = self._cards.pop()
        self.card_stats[card.rank] += 1
        return card


def hand_value(hand):
    total = 0
    aces = 0

    for card in hand:
        total += card.get_value()
        if card.rank == "A":
            aces += 1

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


def format_hand(hand):
    cards = []
    for card in hand:
        cards.append(str(card))
    return "  ".join(cards)


def ask_choice(prompt, choices):
    while True:
        answer = input(prompt).strip().lower()
        for result in choices:
            if answer in choices[result]:
                return result
        print("输入无效，请重新选择。")


def ask_number(prompt, minimum, maximum):
    while True:
        answer = input(prompt).strip()
        try:
            number = int(answer)
        except ValueError:
            print("请输入一个整数。")
            continue

        if minimum <= number <= maximum:
            return number
        print("请输入", minimum, "到", maximum, "之间的数字。")


def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21


def can_split(hand):
    if len(hand) != 2:
        return False
    return hand[0].get_value() == hand[1].get_value()


def strategy_tip(hand, dealer_card, can_double):
    """给出一条容易理解的基础策略提示。"""

    total = hand_value(hand)
    dealer_value = dealer_card.get_value()

    if can_double and total in [10, 11]:
        return "建议：加倍"
    if total <= 11:
        return "建议：要牌"
    if total >= 17:
        return "建议：停牌"
    if dealer_value >= 7:
        return "建议：要牌"
    return "建议：停牌"


def show_table(player_name, hands, dealer, hide_dealer):
    print("\n" + "─" * 42)

    if hide_dealer:
        print("庄家：", dealer[0], " [暗牌]", sep="")
    else:
        print("庄家：", format_hand(dealer), " （", hand_value(dealer), " 点）", sep="")

    hand_number = 1
    for hand_info in hands:
        label = player_name
        if len(hands) > 1:
            label += " 手牌" + str(hand_number)
        print(
            label,
            "：",
            format_hand(hand_info["cards"]),
            " （",
            hand_value(hand_info["cards"]),
            " 点，下注 ",
            hand_info["bet"],
            "）",
            sep="",
        )
        hand_number += 1

    print("─" * 42)


def determine_result(player_hand, dealer_hand):
    player_total = hand_value(player_hand)
    dealer_total = hand_value(dealer_hand)

    if player_total > 21:
        return "loss"
    if dealer_total > 21 or player_total > dealer_total:
        return "win"
    if player_total < dealer_total:
        return "loss"
    return "draw"


def split_hand(player, hand_info, deck):
    """把一手牌拆成两手，并补发一张牌。"""

    player["chips"] -= hand_info["bet"]
    first_card = hand_info["cards"][0]
    second_card = hand_info["cards"][1]

    first_hand = {"cards": [first_card, deck.deal()], "bet": hand_info["bet"]}
    second_hand = {"cards": [second_card, deck.deal()], "bet": hand_info["bet"]}
    return [first_hand, second_hand]


def play_one_hand(player, hand_info, dealer, deck, hand_number):
    """让一名玩家操作一手牌。"""

    hand = hand_info["cards"]

    while hand_value(hand) < 21:
        can_double = len(hand) == 2 and player["chips"] >= hand_info["bet"]
        print("\n", player["name"], "的手牌", hand_number, sep="")
        print("你的牌：", format_hand(hand), "（", hand_value(hand), " 点）", sep="")
        print("庄家明牌：", dealer[0], sep="")
        print(strategy_tip(hand, dealer[0], can_double))

        choices = {
            "hit": ["h", "hit", "要牌"],
            "stand": ["s", "stand", "停牌"],
        }
        prompt = "请选择：[H] 要牌 / [S] 停牌"

        if can_double:
            choices["double"] = ["d", "double", "加倍"]
            prompt += " / [D] 加倍"
        prompt += "："

        action = ask_choice(prompt, choices)

        if action == "stand":
            break

        if action == "double":
            extra_bet = hand_info["bet"]
            player["chips"] -= extra_bet
            hand_info["bet"] += extra_bet
            new_card = deck.deal()
            hand.append(new_card)
            print("加倍成功，你抽到了：", new_card, sep="")
            break

        new_card = deck.deal()
        hand.append(new_card)
        print("你抽到了：", new_card, sep="")

    if hand_value(hand) > 21:
        print(player["name"], "的手牌", hand_number, "爆牌了！")


def settle_hand(player, hand_info, dealer):
    result = determine_result(hand_info["cards"], dealer)
    bet = hand_info["bet"]

    if result == "win":
        player["chips"] += bet * 2
        print(player["name"], "获胜，得到", bet * 2, "筹码。")
    elif result == "draw":
        player["chips"] += bet
        print(player["name"], "与庄家平局，退回", bet, "筹码。")
    else:
        print(player["name"], "本手失败，失去", bet, "筹码。")

    player["scores"][result] += 1


def handle_dealer_blackjack(round_players, dealer):
    """庄家是 Blackjack 时立即结算主注和保险。"""

    print("\n庄家是 Blackjack！")
    print("庄家：", format_hand(dealer), sep="")

    for entry in round_players:
        player = entry["player"]
        hand_info = entry["hands"][0]
        insurance = entry["insurance"]

        if insurance > 0:
            insurance_return = insurance * 3
            player["chips"] += insurance_return
            print(player["name"], "的保险生效，获得", insurance_return, "筹码。")

        if is_blackjack(hand_info["cards"]):
            player["chips"] += hand_info["bet"]
            player["scores"]["draw"] += 1
            print(player["name"], "也是 Blackjack，主注平局。")
        else:
            player["scores"]["loss"] += 1
            print(player["name"], "主注失败。")


def play_round(players, card_stats):
    deck = Deck(card_stats)
    dealer = []
    round_players = []

    print("\n请各位玩家下注。")
    for player in players:
        if player["chips"] <= 0:
            print(player["name"], "没有筹码，本局无法参加。")
            continue

        print("\n", player["name"], "当前有 ", player["chips"], " 筹码。", sep="")
        bet = ask_number("请输入本局赌注：", 1, player["chips"])
        player["chips"] -= bet
        hand_info = {"cards": [], "bet": bet}
        round_players.append(
            {"player": player, "hands": [hand_info], "insurance": 0}
        )

    if not round_players:
        return False

    # 所有玩家和庄家轮流拿两张牌。
    for unused in range(2):
        for entry in round_players:
            entry["hands"][0]["cards"].append(deck.deal())
        dealer.append(deck.deal())

    print("\n庄家明牌：", dealer[0], sep="")
    for entry in round_players:
        show_table(entry["player"]["name"], entry["hands"], dealer, True)

    # 庄家明牌是 A 时，每名玩家都可以购买主注一半金额的保险。
    if dealer[0].rank == "A":
        print("\n庄家明牌是 A，可以购买保险。")
        for entry in round_players:
            player = entry["player"]
            insurance = entry["hands"][0]["bet"] // 2
            if insurance > 0 and player["chips"] >= insurance:
                answer = ask_choice(
                    player["name"] + " 是否花 " + str(insurance) + " 筹码购买保险？[Y/N]：",
                    {"yes": ["y", "yes", "是"], "no": ["n", "no", "否"]},
                )
                if answer == "yes":
                    player["chips"] -= insurance
                    entry["insurance"] = insurance

    if is_blackjack(dealer):
        handle_dealer_blackjack(round_players, dealer)
        return True

    # 庄家没有 Blackjack，已购买的保险失效。
    for entry in round_players:
        if entry["insurance"] > 0:
            print(entry["player"]["name"], "的保险未生效。")

    # 玩家依次操作。每位玩家最多分牌一次。
    for entry in round_players:
        player = entry["player"]
        hand_info = entry["hands"][0]
        print("\n轮到", player["name"], "操作。")

        if can_split(hand_info["cards"]) and player["chips"] >= hand_info["bet"]:
            answer = ask_choice(
                "两张牌点数相同，是否分牌？[Y/N]：",
                {"yes": ["y", "yes", "是", "分牌"], "no": ["n", "no", "否"]},
            )
            if answer == "yes":
                entry["hands"] = split_hand(player, hand_info, deck)
                print("分牌成功，并为两手牌各补发了一张牌。")

        hand_number = 1
        for current_hand in entry["hands"]:
            play_one_hand(player, current_hand, dealer, deck, hand_number)
            hand_number += 1

    print("\n庄家翻开暗牌。")
    print("庄家：", format_hand(dealer), "（", hand_value(dealer), " 点）", sep="")

    has_live_hand = False
    for entry in round_players:
        for hand_info in entry["hands"]:
            if hand_value(hand_info["cards"]) <= 21:
                has_live_hand = True

    if has_live_hand:
        while hand_value(dealer) < 17:
            new_card = deck.deal()
            dealer.append(new_card)
            print("庄家抽到了：", new_card, sep="")
        print("庄家最终点数：", hand_value(dealer), sep="")

    print("\n本局结算：")
    for entry in round_players:
        for hand_info in entry["hands"]:
            settle_hand(entry["player"], hand_info, dealer)

    return True


def show_card_stats(card_stats):
    total = 0
    for rank in RANKS:
        total += card_stats[rank]

    print("\n牌面出现频率（累计发出的牌）：")
    for rank in RANKS:
        count = card_stats[rank]
        if total == 0:
            percent = 0
        else:
            percent = count * 100 / total
        print(rank.rjust(2), "：", str(count).rjust(3), " 次  ", format(percent, ".1f"), "%", sep="")


def save_game(players, card_stats):
    data = {"players": players, "card_stats": card_stats}
    with open(SAVE_FILE, "w", encoding="utf-8") as save_file:
        json.dump(data, save_file, ensure_ascii=False, indent=2)
    print("游戏进度已保存。")


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
    except (OSError, json.JSONDecodeError):
        print("存档读取失败，将开始新游戏。")
        return None

    if "players" not in data or "card_stats" not in data:
        print("存档内容不完整，将开始新游戏。")
        return None
    return data


def create_players():
    player_count = ask_number("请输入玩家人数（2-4）：", 2, 4)
    players = []

    for number in range(1, player_count + 1):
        name = input("请输入玩家" + str(number) + "的名字：").strip()
        if name == "":
            name = "玩家" + str(number)
        players.append(
            {
                "name": name,
                "chips": 1000,
                "scores": {"win": 0, "loss": 0, "draw": 0},
            }
        )
    return players


def show_scores(players):
    print("\n当前战绩：")
    for player in players:
        scores = player["scores"]
        print(
            player["name"],
            "：筹码 ",
            player["chips"],
            " | 胜 ",
            scores["win"],
            " 负 ",
            scores["loss"],
            " 平 ",
            scores["draw"],
            sep="",
        )


def main():
    print("═" * 42)
    print("          欢迎来到二十一点 Blackjack")
    print("═" * 42)

    data = load_game()
    if data is not None:
        answer = ask_choice(
            "检测到存档，是否继续上次游戏？[Y/N]：",
            {"yes": ["y", "yes", "是"], "no": ["n", "no", "否"]},
        )
    else:
        answer = "no"

    if answer == "yes":
        players = data["players"]
        card_stats = data["card_stats"]
        print("已载入上次的游戏进度。")
    else:
        players = create_players()
        card_stats = {}
        for rank in RANKS:
            card_stats[rank] = 0

    while True:
        played = play_round(players, card_stats)
        if not played:
            print("所有玩家都没有筹码，游戏结束。")
            break

        show_scores(players)
        show_card_stats(card_stats)
        save_game(players, card_stats)

        again = ask_choice(
            "\n是否继续？[Y] 继续 / [N] 退出：",
            {"yes": ["y", "yes", "是", "继续"], "no": ["n", "no", "否", "退出"]},
        )
        if again == "no":
            break
        print("\n开始新的一局……")

    save_game(players, card_stats)
    print("感谢游玩，再见！")


if __name__ == "__main__":
    main()
