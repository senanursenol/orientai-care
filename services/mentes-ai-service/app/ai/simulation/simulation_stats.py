class SimulationStats:
    """
    Tracks statistics during a patient simulation.
    """

    def __init__(self):

        self.reset()

    # Reset
    def reset(self):

        self.turns = 0

        self.normal = 0
        self.forgetful = 0
        self.confused = 0
        self.anxious = 0
        self.repeated = 0

    # Recording
    def record_turn(self):

        self.turns += 1

    def record_normal(self):

        self.normal += 1

    def record_forgetful(self):

        self.forgetful += 1

    def record_confused(self):

        self.confused += 1

    def record_anxious(self):

        self.anxious += 1

    def record_repeated(self):

        self.repeated += 1

    # Export
    def summary(self):

        return {

            "turns": self.turns,

            "normal": self.normal,

            "forgetful": self.forgetful,

            "confused": self.confused,

            "anxious": self.anxious,

            "repeated": self.repeated

        }
    
    # Pretty Print
    def print_summary(self, patient_name):

        print("\n" + "=" * 50)
        print("SIMULATION SUMMARY")
        print("=" * 50)

        print(f"Patient              : {patient_name}")
        print(f"Conversation Turns   : {self.turns}")
        print(f"Normal Responses     : {self.normal}")
        print(f"Forgetful Responses  : {self.forgetful}")
        print(f"Confused Responses   : {self.confused}")
        print(f"Anxious Responses    : {self.anxious}")
        print(f"Repeated Questions   : {self.repeated}")

        print("=" * 50)