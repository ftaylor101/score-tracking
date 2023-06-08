import os
import wget
import urllib.request
from typing import List

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

    def check_sessions_exist(self, year: str, race: str, session: str) -> bool:
        """
        Uses the arguments given to form a URL and check its validity.

        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: Boolean, True if a session exists, otherwise False.
        """
        url_exists = False
        while not url_exists:
            if session == "Old style":
                for sess in ["FP1", "FP2", "FP3", "FP4"]:
                    url_exists = self.__check_url_validity(
                        url=f"https://www.motogp.com/en/gp-results/{year}/{race}/MotoGP/{sess}/Classification"
                    )
            elif session == "New style":
                for sess in ["P1", "P2", "FP"]:
                    url_exists = self.__check_url_validity(
                        url=f"https://www.motogp.com/en/gp-results/{year}/{race}/MotoGP/{sess}/Classification"
                    )
            else:
                print("No sessions found")
                break

        return url_exists

    def retrieve_file(self, year: str, race: str, session: str) -> List[str]:
        """
        Gets the PDF from the website.

        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: The pdf name saved locally
        """
        if session == "Old style":
            sessions = ["FP1", "FP2", "FP3", "FP4"]
        elif session == "New style":
            sessions = ["P1", "P2", "FP"]
        else:
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
