from typing import List, Tuple
from scrape_motogp import MotoScraper
from utils.Parser import PdfParser
from utils.Retriever import PdfRetriever
from firestore_management import FirestoreDatabaseManager
import json
import pandas as pd
from tqdm import tqdm


class PointsKeeper:
    """
    A class to gather race results from the web and assign points to each player for their respective riders.
    Scores are kept in a database.
    """

    def __init__(self):
        """
        Hardcoded files contain replacement riders.
        """
        # todo remove this scraper and get the final standings from PDFs
        self.moto_scraper = MotoScraper()

        self.results_getter = PdfParser()
        self.pdf_getter = PdfRetriever()
        self.fdb_manager = FirestoreDatabaseManager()

        # TODO clean up race_num and race_code and the use of dict below and race_names.json
        self.__race_number = {
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

        with open("replacement_riders.json", "r") as json_file:
            self.replacement_riders = json.load(json_file)

        with open("race_names.json", "r") as json_file:
            self.race_names = json.load(json_file)

    def update_points(self, race_num: int = None, year: int = 2022, final_race: bool = False) -> None:
        """
        A method to update the points for each player for the race given by the race code for the given year.

        # todo split this up it is too big and doing too much

        Args:
            race_num: Three letter string defining the race from which to gather results.
            year: Calendar year for the season.
            final_race: Boolean indicating if it is the final race. If so, bonus points are calculated.
        """
        # scrape results for all races
        race_code = self.__race_number[race_num]

        # get race result pdfs
        file_names = dict()
        for moto_class in ["Moto3", "Moto2", "MotoGP Sprint", "MotoGP Race"]:
            fname = self.pdf_getter.retrieve_race_files(
                year=str(year),
                race=race_code,
                category=moto_class,
                session_type="results"
            )
            file_names[moto_class] = fname

        tmp_race_results = {
            "motogp": self.results_getter.parse_race_results_pdf(file_names["MotoGP Race"]),
            "motogp_sprint": self.results_getter.parse_race_results_pdf(file_names["MotoGP Sprint"]),
            "moto2": self.results_getter.parse_race_results_pdf(file_names["Moto2"]),
            "moto3": self.results_getter.parse_race_results_pdf(file_names["Moto3"])
        }

        race_results = {k: v for k, v in tmp_race_results.items() if isinstance(v, pd.DataFrame)}
        categories = ("motogp", "motogp_sprint", "moto2", "moto3")
        score_has_been_updated = list()  # used to avoid multiple updates to the same rider

        # assign scores for each player
        player_names = self._get_player_names()
        for name in tqdm(player_names):
            picks = self._get_player_picks(name)
            all_points = list()
            for single_category in categories:
                replacements = self.replacement_riders[single_category]
                points = race_results[single_category]
                player_picks = self._get_category_picks(single_category, picks)  # returns a list of 3 names
                if single_category != "motogp_sprint":
                    points_store = dict()
                for rider in player_picks:
                    try:
                        rider_points = float(points[points["Rider"].str.
                                             contains(rider, na=False, case=False)]["Points"].iloc[0])
                    except IndexError:
                        # do replacement rider check here
                        if rider in replacements.keys():
                            new_rider = replacements[rider]
                            if new_rider not in player_picks:
                                try:
                                    rider_points = float(points[points["Rider"].str.
                                                         contains(new_rider, na=False, case=False)]["Points"].iloc[0])
                                except IndexError:
                                    rider_points = 0
                            elif new_rider in player_picks:
                                # if new_rider in replacements.keys():  # 'if' not needed as impossible situation
                                new_replacement_rider = replacements[new_rider]
                                try:
                                    rider_points = float(points[points["Rider"].str.
                                                         contains(new_replacement_rider, na=False, case=False)]
                                                         ["Points"].iloc[0])
                                except IndexError:
                                    rider_points = 0
                            else:
                                rider_points = 0
                        else:
                            rider_points = 0
                    if single_category == "motogp_sprint":
                        points_store[rider] = points_store[rider] + rider_points
                    else:
                        points_store[rider] = rider_points
                if single_category == "motogp":
                    continue

                if single_category == "motogp_sprint":
                    single_category = "motogp"
                points_store["category"] = single_category
                all_points.append(points_store)

            # update db here for player scores
            player_ref = self.fdb_manager.db.collection("players").document(name)

            # reset all current week scores
            player_ref.update({"current_week": 0})
            player_ref.update({"current_week_motogp": 0})
            player_ref.update({"current_week_moto2": 0})
            player_ref.update({"current_week_moto3": 0})

            # update db here for rider scores
            current_category = None
            current_week_value = 0
            current_player_scores = player_ref.get().to_dict()

            for category in all_points:
                player_scores = 0
                for rider in category.keys():
                    if rider in score_has_been_updated:
                        player_scores += category[rider]
                        continue
                    elif rider == "category":
                        current_category = category[rider]
                        continue
                    else:
                        rider_doc = self.fdb_manager.db.collection("scores").document(rider)
                        rider_doc.update({self.race_names[race_code]: category[rider]})
                        player_scores += category[rider]
                        score_has_been_updated.append(rider)

                for key in current_player_scores.keys():
                    if key.split("_")[-1] == current_category:
                        player_ref.update({key: player_scores})  # update single category
                        current_week_value += player_scores  # track weekly total

            player_ref.update({"current_week": current_week_value})  # update weekly total
            player_ref.update({self.race_names[race_code]: current_week_value})  # keep track of each week's score
            player_points_total = 0
            for race_number in range(1, race_num + 1):
                race_three_letter_code = self.__race_number[race_number]
                race_reference = self.race_names[race_three_letter_code]
                try:
                    player_points_total += current_player_scores[race_reference]
                except KeyError:
                    continue
            # current_total = current_player_scores["total"]
            player_ref.update({"total": player_points_total})

        if final_race:
            self._calculate_bonus_points(year)

        # update record of current race number
        self.fdb_manager.db.collection("race update").document("current race number").update({"race": race_num})

    def _calculate_bonus_points(self, year: int) -> None:
        """
        A method to allocate bonus points depending on whether the player has picked the correct rider for their
        final championship position or if they have picked all three of the top riders but not in the correct position.

        Args:
            year: The year for which to calculate bonus points.
        """
        # todo update the way to get the points
        with self.moto_scraper as ms:
            tmp_final_standings = {
                "motogp": ms.scrape_final_standings(year=f"{year}", category="MotoGP"),
                "moto2": ms.scrape_final_standings(year=f"{year}", category="Moto2"),
                "moto3": ms.scrape_final_standings(year=f"{year}", category="Moto3")
            }
        final_standings = {k: v for k, v in tmp_final_standings.items() if isinstance(v, pd.DataFrame)}

        categories = list(final_standings.keys())

        # assign scores for each player
        player_names = self._get_player_names()
        for name in tqdm(player_names):
            picks = self._get_player_picks(name)
            for single_category in categories:
                thirty_bonus_tracker = list()
                champ_standings = final_standings[single_category]
                player_picks = self._get_category_picks(single_category, picks)  # returns a list of 3 names
                for idx in range(len(player_picks)):
                    if player_picks[idx] == champ_standings["Rider"].iloc[idx]:
                        self._insert_bonus_point(bonus=50, player=name, rider=player_picks[idx])
                        thirty_bonus_tracker.append(False)
                        print(f"50 points for {name} with {player_picks[idx]} in "
                              f"{champ_standings['Position'].iloc[idx]} place")
                    elif champ_standings["Rider"].str.contains(player_picks[idx]).any():
                        thirty_bonus_tracker.append(True)
                    else:
                        thirty_bonus_tracker.append(False)

                if all(thirty_bonus_tracker):
                    for rider in player_picks:
                        self._insert_bonus_point(bonus=10, player=name, rider=rider)
                    print(f"Congrats - 30 bonus points for {name} in {single_category}")
                else:
                    print(f"No 30 bonus points for {name} in {single_category}")

    def _insert_bonus_point(self, bonus: int, player: str, rider: str) -> None:
        """
        A method to insert the provided bonus points for the given player and their rider.

        Args:
            bonus: The number of points to award the player for a correct pick.
            player: The player receiving the bonus points.
            rider: The rider who finished in the expected position or in the top three.
        """
        bonus_name = "bonus_50 "if bonus == 50 else "bonus_30"
        doc_ref = self.fdb_manager.db.collection("players")
        current_bonus = doc_ref.document(player).get().to_dict()[bonus_name]
        doc_ref.document(player).update({bonus_name: current_bonus + bonus})

    def _get_player_names(self) -> List:
        """
        A method to query the firestore database for all players.

        Returns:
            A distinct list of player names
        """
        doc_ref = self.fdb_manager.db.collection("players")
        list_of_names = [doc.id for doc in doc_ref.stream()]
        return list_of_names

    def _get_player_picks(self, name: str) -> List[Tuple]:
        """
        A method to retrieve the rider picks for all categories for the given player.

        Args:
            name: the player name for which to get rider picks

        Returns:
            A list of tuples: (category, rider name)
        """
        doc_ref = self.fdb_manager.db.collection("picks")
        player_picks = [(k, v) for k, v in doc_ref.document(name).get().to_dict().items()]
        return player_picks

    @staticmethod
    def _tuple_sort(tuple_input: Tuple):
        """
        A helper to sort a list of tuples by a specific element in the tuple.

        Args:
            tuple_input: A tuple in the list to be sorted.

        Returns:
            The value on which to sort.
        """
        return tuple_input[0]

    def _get_category_picks(self, category: str, picks: List[Tuple]) -> List:
        """
        A method to find the riders chosen for a particular category.

        Args:
            category: the category for which to find riders for
            picks: the list containing the tuples of riders and their racing categories

        Returns:
            a list of riders
        """
        category = "motogp" if category == "motogp_sprint" else category
        player_picks = list()
        picks.sort(key=self._tuple_sort)
        for pick in picks:
            if pick[0].split("_")[0] == category:
                player_picks.append(pick[1])
        return player_picks


if __name__ == "__main__":
    pk = PointsKeeper()
    race = 10
    pk.update_points(race_num=race, year=2023, final_race=False)
    # pk.summarise_points(race_num=race)
