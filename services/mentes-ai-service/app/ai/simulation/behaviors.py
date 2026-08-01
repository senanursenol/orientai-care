import random


class BehaviorEngine:
    def __init__(self):
        self.repeat_probability = 0.25
        self.confusion_probability = 0.30
        self.anxiety_probability = 0.20

    def should_repeat(self):
        return random.random() < self.repeat_probability

    def should_confuse(self):
        return random.random() < self.confusion_probability

    def should_be_anxious(self):
        return random.random() < self.anxiety_probability