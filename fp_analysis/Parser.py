import fitz
import re
import pandas as pd


class PdfParser:
    """
    This class reads in MotoGP free practice session PDFs and extracts the lap time data for each rider and makes it
    available for use via a Pandas dataframe.
    """

    def __init__(self):
        self.threshold = 1000

    @staticmethod
    def _min_to_seconds(laptime: str) -> float:
        """
        Convert a lap time given as a string in minutes'seconds.milliseconds into a float in seconds.

        :param laptime: the time in m'ss.000
        :return: the lap time as a float in seconds ss.000
        """
        minsec = laptime.split("'")
        sec = round(int(minsec[0]) * 60 + float(minsec[1]), 3)
        return sec

    @staticmethod
    def _trim_names(name: str) -> str:
        """
        Remove a newline \n character and practice positions to leave just a name.

        Sometimes the regex returns the team name and with or without a leading \n character so always count from the
        end.

        :param name: The string with \n and position included.
        :return: Just a firstname and surname as a single string.
        """
        split_name = name.split("\n")
        return split_name[-2]

    @staticmethod
    def _trim_laptimes(lap_time: str) -> str:
        """
        Remove all \n newline characters and lap numbers to leave only lap times.

        :param lap_time: The lap time with newline \n and lap numbers.
        :return: The lap time as a string.
        """
        split_lap = lap_time.split("\n")
        return split_lap[1]

    def parse_pdf(self, file: str, delete_if_less_than_three: bool) -> pd.DataFrame:
        """
        This method accepts a PDF and returns a dataframe with all riders and their lap times and tyre information.

        :param file: The file path including file name and extension to the practice session file.
        :param delete_if_less_than_three:
            Delete the rider's lap times if only less than three laps exist. Only useful for practice sessions.
        :return: a dataframe
        """
        with fitz.Document(file) as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        # Nationality three-letter code proceeds the name, the rider first names start with a capital, surnames are all
        # uppercase and position (1st, 2nd, 3rd, ...) always follows
        rider_name_pattern = r"[A-Z]{3}\s{1}[\w\s]+\s\d{1,2}[stndrh]{2,}"
        riders_with_position = re.findall(rider_name_pattern, text)
        riders_names_only = list()
        for rider in riders_with_position:
            riders_names_only.append(self._trim_names(rider))

        # split the text on the rider names to get each rider's lap time info
        rider_data = re.split(rider_name_pattern, text)  # text data from each rider
        rider_data.pop(0)  # delete all data before the first rider as it only contains circuit information

        # ignore pit in laps
        lap_time_pattern = r"\s[1-2]'\d\d.\d\d\d\s\d{1,2}\s"  # only accept laps that are in the 1-2 min range incl.
        rider_lap_times = list()  # must be same length as rider_names_only
        for lap_time_string in rider_data:
            stint_times = re.split(r"\nP\n", lap_time_string)  # split lap times on pit entries
            number_of_stints = len(stint_times)
            lap_time_float = list()
            for i, times in enumerate(stint_times):
                if i == number_of_stints - 1:  # last stint so get all times
                    rider_lap_time_string = re.findall(lap_time_pattern, times)
                else:
                    # remove the last time as that is pit in
                    rider_lap_time_string = re.findall(lap_time_pattern, times)[:-1]
                # rider_lap_time_string = re.findall(lap_time_pattern, lap_time_string)
                temp_laps = [self._min_to_seconds(self._trim_laptimes(lap)) for lap in rider_lap_time_string]
                lap_time_float.extend(temp_laps)
            rider_lap_times.append(lap_time_float)

        rider_and_lap_time_dict = dict(zip(riders_names_only, rider_lap_times))

        if delete_if_less_than_three:
            # check that each rider has at least 3 laps
            to_delete = list()
            for k, v in rider_and_lap_time_dict.items():
                if len(v) < 3:
                    to_delete.append(k)
            if to_delete:
                for rider_name in to_delete:
                    del rider_and_lap_time_dict[rider_name]

        rider_and_lap_time_df = pd.DataFrame.from_dict(rider_and_lap_time_dict, orient='index').T

        return rider_and_lap_time_df
