import os
import wget
import urllib.request
from typing import List, Union

from urllib.error import HTTPError


class PdfRetriever:
    """
    This class is for retrieving session PDFs for all classes in the MotoGP championship.
    """
    def __init__(self):
        self.session = None
        self.sessions = None

        self.categories = {
            "MotoGP Race": "MotoGP",
            "MotoGP Sprint": "MotoGP",
            "Moto2": "Moto2",
            "Moto3": "Moto3",
        }
        self.session_style = {
            "GP: FP1, PR, FP2, WUP": ["FP1", "PR", "FP2", "WUP"],
            "GP: P1, P2, FP, WUP": ["P1", "P2", "FP", "WUP"],
            "GP: FP1, FP2, FP3, FP4, WUP": ["FP1", "FP2", "FP3", "FP4", "WUP"],
            "GP: FP1, FP2, FP3, WUP": ["FP1", "FP2", "FP3", "WUP"],
            "2: FP1, PR, FP2, WUP": ["FP1", "PR", "FP2", "WUP"],
            "2: P1, P2, P3": ["P1", "P2", "P3"],
            "2: FP1, FP2, FP3, WUP": ["FP1", "FP2", "FP3", "WUP"],
            "3: FP1, PR, FP2, WUP": ["FP1", "PR", "FP2", "WUP"],
            "3: P1, P2, P3": ["P1", "P2", "P3"],
            "3: FP1, FP2, FP3, WUP": ["FP1", "FP2", "FP3", "WUP"]
        }

    @staticmethod
    def __check_url_validity(url: str) -> bool:
        """
        Helper function to verify if a URL is valid.

        :param url: The URL to check.
        :return: True if URL is valid, False otherwise.
        """
        print(url)
        exist = False

        try:
            code = urllib.request.urlopen(url).getcode()
        except HTTPError:
            code = 404

        if code == 200:
            exist = True

        return exist

    def check_sessions_exist(self, category: str, year: int, race: str, session: Union[List[str], str]) -> bool:
        """
        Uses the arguments given to form a URL and check the practice session validity.

        :param category: The name of the racing class.
        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: Boolean, True if a session exists, otherwise False.
        """
        url_exists = False

        if isinstance(session, str):
            if "SPR" == session or "RAC" == session:
                session_types = [session]
            else:
                session_types = self.session_style[session]
        elif isinstance(session, list):
            session_types = session
        else:
            print("Incorrect session type")
            return False
        while not url_exists:
            for sess in session_types:
                url_exists = self.__check_url_validity(
                    url=f"https://www.motogp.com/en/gp-results/{year}/{race}/{category}/{sess}/Classification"
                )
                if url_exists:
                    print(f"{category}-{year}-{race}-{sess} exist: {url_exists}")
                else:
                    print(f"No session found for {sess} in {category}-{year}-{race}-{sess}")
            if not url_exists:
                print(f"No sessions found for {category}-{year}-{race}")
                break

        return url_exists

    # def check_race_exist(self, year: int, race: str, category: str) -> bool:
    #     """
    #     Uses the arguments given to form a URL and check the validity of the results page for the race.
    #
    #     :param year: The year of the desired race.
    #     :param race: The race's 3-letter code.
    #     :param category: The category of the race.
    #     :return: Boolean, True if a race and /or sprint exists, otherwise False.
    #     """
    #     sess = "SPR" if category == "MotoGP Sprint" else "RAC"
    #     race_class = self.categories[category]
    #
    #     url_exists = self.__check_url_validity(
    #         url=f"https://www.motogp.com/en/gp-results/{year}/{race}/{race_class}/{sess}/Classification"
    #     )
    #     if not url_exists:
    #         print(f"No {category} race found")
    #
    #     return url_exists

    def retrieve_practice_files(
            self, category: str, year: int, race: str, session: Union[List[str], str]) -> List[str]:
        """
        Gets the PDF from the website.

        :param category: The racing class for which to get the session file.
        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: The pdf name saved locally
        """
        if isinstance(session, str):
            sessions = self.session_style[session]
        elif isinstance(session, list):
            sessions = session
        else:
            raise ValueError("Error in Retriever - incorrect session types")

        file_names = list()

        for sess in sessions:
            url = f"https://resources.motogp.com/files/results/{year}/{race}/{category}/{sess}/Analysis.pdf"
            valid_url = self.__check_url_validity(url)
            if valid_url:
                download_name = (r"../score-tracking/static/" + f"{category}-{year}_{race}_{sess}.pdf")
                if os.path.isfile(download_name):
                    file_name = download_name
                else:
                    file_name = wget.download(url, download_name)
                file_names.append(file_name)

        return file_names

    def retrieve_race_files(self, category: str, year: int, race: str, race_type: str, data_type: str)\
            -> Union[str, None]:
        """
        Gets the PDF from the website for race pace analysis or race results.

        :param category: The racing class for which to get race files.
        :param year: The year of the desired race.
        :param race: The race of the desired race.
        :param race_type: The category of the desired race.
        :param data_type:
            The type of document retrieved, either race pace ("analysis") or finishing order ("results").
        :return: The pdf name saved locally or None if no analysis file exists.
        """
        name = "Analysis" if data_type == "analysis" else "Classification"

        url = \
            f"https://resources.motogp.com/files/results/{year}/{race}/{category}/{race_type}/{name}.pdf"
        valid_url = self.__check_url_validity(url)
        file_name = None
        if valid_url:
            download_name = (r"../score-tracking/static/" + f"{year}_{race}_{category}_{race_type}_{name}.pdf")
            if os.path.isfile(download_name):
                file_name = download_name
            else:
                file_name = wget.download(url=url, out=download_name)

        return file_name
