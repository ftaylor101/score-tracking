import json
from typing import Dict, List

import firebase_admin
from firebase_admin import firestore, credentials


class PicksParser:
    """
    A class to hold rider and player details for convenience upload to firestore
    """
    def __init__(self, name: str, class_name: str, predicted: int, picked_by: str):
        self.name = name
        self.class_name = class_name
        self.championship_position = 0
        self.predicted_championship_position = predicted
        self.picked_by = picked_by

    @classmethod
    def create_rider(cls, name: str, class_name: str, predicted_position: int, picked_by: str) -> "PicksParser":
        return cls(name, class_name, predicted_position, picked_by)

    @classmethod
    def from_picks_dict(cls, player_dict: Dict) -> List["PicksParser"]:
        """
        Creates a list of riders based on player picks.
        Dictionary has the format:
            {PlayerName:
                {ClassName: [rider_1, rider_2, rider_3],
                ClassName: [...]
                },
            PlayerName:
                {...
                }
            }
        Args:
            player_dict: a dictionary with player picks by class name

        Returns: a list of rider objects
        """
        rider_list = list()
        for player in player_dict.keys():
            player_picks = player_dict[player]
            for class_name in player_picks.keys():
                class_picks = player_picks[class_name]
                for i, rider in enumerate(class_picks):
                    rider_list.append(PicksParser.create_rider(rider, class_name, int(i + 1), player))

        return rider_list

    @classmethod
    def from_json(cls, file_path: str) -> List["PicksParser"]:
        """
        Parses a json file to extract players names and their picks.
        Args:
            file_path: the location of the picks including name and extension
        Returns: a list of picks
        """
        with open(file_path, encoding="utf-8") as file:
            player_picks = json.load(file)
        return PicksParser.from_picks_dict(player_picks)

    def riders_to_dict(self) -> Dict:
        """
        Returns: the rider as a dictionary.
        """
        return dict(class_name=self.class_name, championship_position=self.championship_position)

    @staticmethod
    def players_to_dict() -> Dict:
        """
        Returns: the player's initial scores as a dictionary with all scores initialised to 0.
        """
        return dict(
            total=0,
            bonus_50=0,
            bonus_30=0,
            current_week_motogp=0,
            current_week_moto2=0,
            current_week_moto3=0,
            current_week=0
        )

    def picks_to_dict(self) -> Dict:
        """
        Returns: the picks as values and class and predicted position as keys.
        """
        return {self.class_name + "_" + str(self.predicted_championship_position): self.name}


class FirestoreDatabaseManager:
    """
    A class to handle interactions with the Google Cloud Firestore database.
    """
    def __init__(self):
        # Authenticate and get firestore client
        with open("db-key.json", "r") as file:
            key_dict = json.load(file)
        self.db = self.__init_with_service_account(key_dict)
        self.data = None

    @staticmethod
    def __init_with_service_account(cred_dict: Dict):
        """
        Initialize the Firestore DB client using a service account

        Args:
            cred_dict: dictionary with credentials
        Returns:
            firestore db client
        """
        cred = credentials.Certificate(cred_dict)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)
        return firestore.client()

    def get_picks_data(
            self, pick_file_path: str = r"players_2023.json")\
            -> None:
        """
        Get the data regarding players and their picks.
        Args:
            pick_file_path: the path to the json data
        """
        self.data = PicksParser.from_json(pick_file_path)

    def create_scores_collection(self) -> None:
        """
        Create the scores collection that holds rider names as documents and their class and position etc. as fields.
        """
        scores_ref = self.db.collection('scores')
        processed_riders = []
        for rider in self.data:
            if rider.name in processed_riders:
                continue  # skip to next rider
            processed_riders.append(rider.name)
            scores_ref.document(rider.name).set(rider.riders_to_dict())

    def create_players_collection(self) -> None:
        """
        Create the players collections that holds the player name as documents and their scores achieved over the
        season as fields.
        """
        players_ref = self.db.collection('players')
        player_names = []
        for player in self.data:
            if player.picked_by in player_names:
                continue  # only set up each player once
            player_names.append(player.picked_by)
            players_ref.document(player.picked_by).set(player.players_to_dict())

    def create_picks_collection(self) -> None:
        """
        Create a picks collection that contains the player names as documents and their choices as fields.
        """
        picks_ref = self.db.collection('picks')
        for pick in self.data:
            picks_ref.document(pick.picked_by).set(pick.picks_to_dict(), merge=True)

    def get_scores_collection(self, d: dict) -> dict:
        """
        Form the Scores collection that consists of riders and their details based on player picks.

        Args:
            d: dictionary containing player picks.

        Returns: a dictionary with names of riders and fields associated with them.
        """
        pass


if __name__ == "__main__":
    fdb = FirestoreDatabaseManager()
    fdb.get_picks_data()
    fdb.create_scores_collection()
    fdb.create_players_collection()
    fdb.create_picks_collection()
