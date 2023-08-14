class RaceResources:
    """
    A resource of race names, three-letter codes and their even number.
    """
    def __init__(self):
        self.race_names = {
            "POR": "1_POR",
            "ARG": "2_ARG",
            "AME": "3_AME",
            "SPA": "4_SPA",
            "FRA": "5_FRA",
            "ITA": "6_ITA",
            "GER": "7_GER",
            "NED": "8_NED",
            "KAZ": "9_KAZ",
            "GBR": "10_GBR",
            "AUT": "11_AUT",
            "CAT": "12_CAT",
            "RSM": "13_RSM",
            "IND": "14_IND",
            "JPN": "15_JPN",
            "INA": "16_INA",
            "AUS": "17_AUS",
            "THA": "18_THA",
            "MAL": "19_MAL",
            "QAT": "20_QAT",
            "VAL": "21_VAL"
        }

        self.race_number = {
            1: "POR",
            2: "ARG",
            3: "AME",
            4: "SPA",
            5: "FRA",
            6: "ITA",
            7: "GER",
            8: "NED",
            9: "KAZ",
            10: "GBR",
            11: "AUT",
            12: "CAT",
            13: "RSM",
            14: "IND",
            15: "JPN",
            16: "INA",
            17: "AUS",
            18: "THA",
            19: "MAL",
            20: "QAT",
            21: "VAL"
        }

    def number_to_name(self, race_number: int) -> str:
        """
        Take an event number and return the number + name as a string.

        :param race_number: The race number (i.e. its position in the calendar).
        :return: String of the number + 3-letter code.
        """
        return self.race_names[self.race_number[race_number]]
