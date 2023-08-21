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
            "GBR": "9_GBR",
            "AUT": "10_AUT",
            "CAT": "11_CAT",
            "RSM": "12_RSM",
            "IND": "13_IND",
            "JPN": "14_JPN",
            "INA": "15_INA",
            "AUS": "16_AUS",
            "THA": "17_THA",
            "MAL": "18_MAL",
            "QAT": "19_QAT",
            "VAL": "20_VAL"
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
            9: "GBR",
            10: "AUT",
            11: "CAT",
            12: "RSM",
            13: "IND",
            14: "JPN",
            15: "INA",
            16: "AUS",
            17: "THA",
            18: "MAL",
            19: "QAT",
            20: "VAL"
        }

    def number_to_name(self, race_number: int) -> str:
        """
        Take an event number and return the number + name as a string.

        :param race_number: The race number (i.e. its position in the calendar).
        :return: String of the number + 3-letter code.
        """
        return self.race_names[self.race_number[race_number]]
