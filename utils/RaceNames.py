class RaceResources:
    """
    A resource of race names, three-letter codes and their even number.
    """
    def __init__(self):
        self.race_names = {
            "THA": "1_THA",
            "ARG": "2_ARG",
            "AME": "3_AME",
            "QAT": "4_QAT",
            "SPA": "5_SPA",
            "FRA": "6_FRA",
            "GBR": "7_GBR",
            "ARA": "8_ARA",
            "ITA": "9_ITA",
            "NED": "10_NED",
            "GER": "11_GER",
            "CZE": "12_CZE",
            "AUT": "13_AUT",
            "HUN": "14_HUN",
            "CAT": "15_CAT",
            "RSM": "16_RSM",
            "JPN": "17_JPN",
            "INA": "18_INA",
            "AUS": "19_AUS",
            "MAL": "20_MAL",
            "POR": "21_POR",
            "VAL": "22_SLD"
        }

        self.race_number = {
            1: "THA",
            2: "ARG",
            3: "AME",
            4: "QAT",
            5: "SPA",
            6: "FRA",
            7: "GBR",
            8: "ARA",
            9: "ITA",
            10: "NED",
            11: "GER",
            12: "AUT",
            13: "CZE",
            14: "HUN",
            15: "CAT",
            16: "RSM",
            17: "JPN",
            18: "INA",
            19: "AUS",
            20: "MAL",
            21: "POR",
            22: "VAL"
        }

    def number_to_name(self, race_number: int) -> str:
        """
        Take an event number and return the number + name as a string.

        :param race_number: The race number (i.e. its position in the calendar).
        :return: String of the number + 3-letter code.
        """
        return self.race_names[self.race_number[race_number]]
