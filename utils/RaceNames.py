class RaceResources:
    """
    A resource of race names, three-letter codes and their even number.
    """
    def __init__(self):
        self.race_names = {
            "QAT": "1_QAT",
            "POR": "2_POR",
            "AME": "3_AME",
            "SPA": "4_SPA",
            "FRA": "5_FRA",
            "CAT": "6_CAT",
            "ITA": "7_ITA",
            "KAZ": "8_KAZ",
            "NED": "9_NED",
            "GER": "10_GER",
            "GBR": "11_GBR",
            "AUT": "12_AUT",
            "ARA": "13_ARA",
            "RSM": "14_RSM",
            "IND": "15_IND",
            "INA": "16_INA",
            "JPN": "17_JPN",
            "AUS": "18_AUS",
            "THA": "19_THA",
            "MAL": "20_MAL",
            "VAL": "21_VAL"
        }

        self.race_number = {
            1: "QAT",
            2: "POR",
            3: "AME",
            4: "SPA",
            5: "FRA",
            6: "CAT",
            7: "ITA",
            8: "KAZ",
            9: "NED",
            10: "GER",
            11: "GBR",
            12: "AUT",
            13: "ARA",
            14: "RSM",
            15: "IND",
            16: "INA",
            17: "JPN",
            18: "AUS",
            19: "THA",
            20: "MAL",
            21: "VAL"
        }

    def number_to_name(self, race_number: int) -> str:
        """
        Take an event number and return the number + name as a string.

        :param race_number: The race number (i.e. its position in the calendar).
        :return: String of the number + 3-letter code.
        """
        return self.race_names[self.race_number[race_number]]
