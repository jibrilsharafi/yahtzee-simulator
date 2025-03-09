class Dice:
    def __init__(self):
        self.value = 1

    def roll(self):
        import random
        self.value = random.randint(1, 6)
        return self.value

    def get_value(self):
        return self.value