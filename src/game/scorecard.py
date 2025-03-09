class Scorecard:
    def __init__(self):
        self.scores = {
            "ones": None,
            "twos": None,
            "threes": None,
            "fours": None,
            "fives": None,
            "sixes": None,
            "three_of_a_kind": None,
            "four_of_a_kind": None,
            "full_house": None,
            "small_straight": None,
            "large_straight": None,
            "yahtzee": None,
            "chance": None
        }

    def calculate_score(self, category, dice):
        if category == "ones":
            return dice.count(1) * 1
        elif category == "twos":
            return dice.count(2) * 2
        elif category == "threes":
            return dice.count(3) * 3
        elif category == "fours":
            return dice.count(4) * 4
        elif category == "fives":
            return dice.count(5) * 5
        elif category == "sixes":
            return dice.count(6) * 6
        elif category == "three_of_a_kind":
            return self._three_of_a_kind_score(dice)
        elif category == "four_of_a_kind":
            return self._four_of_a_kind_score(dice)
        elif category == "full_house":
            return self._full_house_score(dice)
        elif category == "small_straight":
            return 30 if self._is_small_straight(dice) else 0
        elif category == "large_straight":
            return 40 if self._is_large_straight(dice) else 0
        elif category == "yahtzee":
            return 50 if self._is_yahtzee(dice) else 0
        elif category == "chance":
            return sum(dice)
        return 0

    def _three_of_a_kind_score(self, dice):
        for die in set(dice):
            if dice.count(die) >= 3:
                return sum(dice)
        return 0

    def _four_of_a_kind_score(self, dice):
        for die in set(dice):
            if dice.count(die) >= 4:
                return sum(dice)
        return 0

    def _full_house_score(self, dice):
        unique_counts = set(dice.count(die) for die in set(dice))
        return 25 if unique_counts == {2, 3} else 0

    def _is_small_straight(self, dice):
        small_straights = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
        return any(small_straight.issubset(set(dice)) for small_straight in small_straights)

    def _is_large_straight(self, dice):
        return set(dice) in [{1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}]

    def _is_yahtzee(self, dice):
        return len(set(dice)) == 1

    def get_scores(self):
        return self.scores

    def set_score(self, category, score):
        if category in self.scores:
            self.scores[category] = score