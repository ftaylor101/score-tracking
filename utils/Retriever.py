import os
import wget
import urllib.request
from typing import List, Union

from urllib.error import HTTPError


class PdfRetriever:
    """
    This class is for retrieving MotoGP Practice Session PDFs.
    """
    def __init__(self):
        self.year = None
        self.race = None
        self.session = None
        self.sessions = None

        self.categories = {
            "MotoGP Race": "MotoGP",
            "MotoGP Sprint": "MotoGP",
            "Moto2": "Moto2",
            "Moto3": "Moto3",
        }
        self.session_style = {
            "Old style": ["FP1", "FP2", "FP3", "FP4", "WUP"],
            "New style": ["P1", "P2", "FP", "WUP"],
            "Latest style": ["FP1", "PR", "FP2", "WUP"]
        }

    @staticmethod
    def __check_url_validity(url: str) -> bool:
        """
        Helper function to verify if a URL is valid.

        :param url: The URL to check.
        :return: True if URL is valid, False otherwise.
        """
        exist = False

        try:
            code = urllib.request.urlopen(url).getcode()
        except HTTPError:
            code = 404

        if code == 200:
            exist = True

        return exist

    def check_motogp_practice_sessions_exist(self, year: int, race: str, session: str) -> bool:
        """
        Uses the arguments given to form a URL and check the MotoGP practice session validity.

        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: Boolean, True if a session exists, otherwise False.
        """
        url_exists = False
        session_types = self.session_style[session]
        while not url_exists:
            for sess in session_types:
                url_exists = self.__check_url_validity(
                    url=f"https://www.motogp.com/en/gp-results/{year}/{race}/MotoGP/{sess}/Classification"
                )
                print(f"{year}-{race}-{sess} exist: {url_exists}")
            else:
                print(f"No sessions found for {sess}")
                break

        return url_exists

    def check_race_exist(self, year: int, race: str, category: str) -> bool:
        """
        Uses the arguments given to form a URL and check the validity of the results page for the race.

        :param year: The year of the desired race.
        :param race: The race's 3-letter code.
        :param category: The category of the race.
        :return: Boolean, True if a race and /or sprint exists, otherwise False.
        """
        sess = "SPR" if category == "MotoGP Sprint" else "RAC"
        race_class = self.categories[category]

        url_exists = self.__check_url_validity(
            url=f"https://www.motogp.com/en/gp-results/{year}/{race}/{race_class}/{sess}/Classification"
        )
        if not url_exists:
            print(f"No {category} race found")

        return url_exists

    def retrieve_practice_files(self, year: int, race: str, session: str) -> List[str]:
        """
        Gets the PDF from the website.

        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: The pdf name saved locally
        """
        try:
            sessions = self.session_style[session]
        except ValueError:
            raise ValueError("Session not set correctly")

        self.year = year
        self.race = race

        file_names = list()

        for sess in sessions:
            url = f"https://resources.motogp.com/files/results/{self.year}/{self.race}/MotoGP/{sess}/Analysis.pdf"
            valid_url = self.__check_url_validity(url)
            if valid_url:
                download_name = r"../score-tracking/static/" + f"{year}_{race}_{sess}.pdf"
                if os.path.isfile(download_name):
                    file_name = download_name
                else:
                    file_name = wget.download(url, download_name)
                file_names.append(file_name)

        return file_names

    def retrieve_race_files(self, year: int, race: str, category: str, session_type: str) -> Union[str, None]:
        """
        Gets the PDF from the website for race pace analysis or race results.

        :param year: The year of the desired race.
        :param race: The race of the desired race.
        :param category: The category of the desired race.
        :param session_type:
            The type of document retrieved, either race pace ("analysis") or finishing order ("results").
        :return: The pdf name saved locally or None if no analysis file exists.
        """
        race_type = "SPR" if category == "MotoGP Sprint" else "RAC"
        race_class = self.categories[category]
        name = "Analysis" if session_type == "analysis" else "Classification"

        self.year = year
        self.race = race

        url = \
            f"https://resources.motogp.com/files/results/{self.year}/{self.race}/{race_class}/{race_type}/{name}.pdf"
        valid_url = self.__check_url_validity(url)
        file_name = None
        if valid_url:
            download_name = r"../score-tracking/static/" + f"{year}_{race}_{race_class}_{race_type}_{name}.pdf"
            if os.path.isfile(download_name):
                file_name = download_name
            else:
                file_name = wget.download(url=url, out=download_name)

        return file_name
