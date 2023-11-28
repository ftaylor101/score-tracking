import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Dict
from copy import deepcopy
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime


col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.write("#### Welcome to Sandra's MotoGP Sweepstake")
    st.write("Points for each player are summarised in the table below. The plotting section shows each player's "
             "cumulative points and scoreboard position after each event.")
# with col2:
#     st.image("Yogo on a motorbike.jpg", caption="Yogo the yoghurt looking cool")


def init_with_service_account(cred_dict: Dict):
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


# Authenticate and get firestore client
key_dict = json.loads(st.secrets["textkey"])
db = init_with_service_account(key_dict)

# region session state setup
if "current_points_df" not in st.session_state:
    st.session_state["current_points_df"] = None
# endregion


# region helper functions
def highlight_column(x: pd.DataFrame):
    """Highlight a particular column of a dataframe."""
    r = f"background-color: #ff9999"
    tmp_df = pd.DataFrame('', index=x.index, columns=x.columns)
    tmp_df.loc[:, "Total"] = r
    return tmp_df


def get_race_number() -> int:
    """
    Function to retrieve the current race number in the database.

    :return:
        A race number as an integer.
    """
    return db.collection("race update").document("current race number").get().to_dict()["race"]


# @st.cache_data
def get_player_points_data(race_number: int) -> pd.DataFrame:
    """
    Function to retrieve player data and their points from the NoSQL db. The race number is used for caching control.

    Args:
        race_number: The most recent race number. If changed, it will re-run this function instead of returning the
        cached dataframe.

    Returns:
        A dataframe with player names and their points for all categories and races.
    """
    print(f"The most recent race number is: {race_number}")

    db_doc_ref = db.collection("players")
    out_df = pd.DataFrame()
    for db_doc in db_doc_ref.stream():
        temp_dict = dict()
        players_dict = db_doc.to_dict()
        for k, v in players_dict.items():
            split_str = k.split("_")
            try:
                temp_dict[(int(split_str[0]), split_str[1])] = v
            except ValueError:
                temp_dict[(0, k)] = v
        temp_df = pd.DataFrame(data=temp_dict, index=[db_doc.id])
        out_df = pd.concat([out_df, temp_df])
    return out_df


@st.cache_data
def get_player_picks_data() -> pd.DataFrame:
    """
    Function to retrieve player choices for each category.

    Returns:
        A dataframe with players names and their choices for each racing category.
    """
    db_doc_ref = db.collection("picks")
    out_df = pd.DataFrame()
    for db_doc in db_doc_ref.stream():
        tmp_dct = {k: [v] for k, v in db_doc.to_dict().items()}
        out_df = pd.concat([out_df, pd.DataFrame(tmp_dct, index=[db_doc.id])])
    return out_df


def show_points():
    """
    Function to collate points and format the dataframe for visual purposes.
    """
    # todo place code in here to get data and format the dataframe
    pass


def move_column(dataframe: pd.DataFrame, column_name: str, new_position: int) -> pd.DataFrame:
    """
    Helper function to move a column to a specified location in a dataframe.

    Args:
        dataframe: The dataframe in which to move the column.
        column_name: The column name.
        new_position: The new column index.

    Returns:
        The dataframe with the columns rearranged.
    """
    col_to_move = dataframe.pop(column_name)
    dataframe.insert(new_position, column_name, col_to_move)
    return dataframe

# endregion


# region cache all data
current_race_number = get_race_number()
score_df = get_player_points_data(current_race_number)
player_picks_df = get_player_picks_data()
# endregion

# region Show current points
st.write("## :racing_motorcycle: Points :racing_motorcycle:")
score_df = score_df.reindex(columns=score_df.columns.sort_values())
score_df.sort_values(by=(0, "total"), ascending=False, inplace=True)
score_df.rename(
    columns={
        "current_week_motogp": "Current week MotoGP",
        "current_week_moto2": "Current week Moto2",
        "current_week_moto3": "Current week Moto3",
        "current_week": "Current week",
        "total": "Total"
    },
    inplace=True
)

st.write("Final points with bonus points")
st.dataframe(score_df)

# organising the dataframe
to_remove = [(0, "bonus_30"), (0, "bonus_50")]
display_df = score_df.drop(columns=to_remove)
display_df = display_df.reindex(columns=sorted(display_df.columns))

display_df[("Player", "Player")] = display_df.index
display_df.index = pd.RangeIndex(1, len(display_df.index) + 1)
display_df = display_df.droplevel(level=0, axis="columns")

# styling the dataframe
display_df = move_column(display_df, "Player", 0)
float_cols = display_df.columns[1:]  # Player name column has been set as the first column
formatted_df = display_df.style.format('{:.0f}', subset=float_cols)
formatted_df.apply(highlight_column, axis=None)

st.dataframe(formatted_df, use_container_width=True)
# endregion

# region points per race per rider
# rider points per race
scores_doc_ref = db.collection("scores")
all_scores = list()
banned_keys = ["championship_position", "class_name"]
for score_doc in scores_doc_ref.stream():
    tmp_dict = score_doc.to_dict()
    tmp_dict_keys = tuple(tmp_dict.keys())
    for k in tmp_dict_keys:
        if k in banned_keys:
            del tmp_dict[k]
    all_scores.append(
        {"Rider": score_doc.id,
         "Points": tmp_dict})
with st.expander("Points per rider"):
    st.write("This section shows the points per rider per race. If a rider was replaced for a race then the rider "
             "scores the points gained by the replacement.")
    st.write(all_scores)
# endregion

# region Plotting
st.write("## :chart_with_upwards_trend: Plots :chart_with_downwards_trend:")
to_drop = ["Current week MotoGP", "Current week Moto2", "Current week Moto3", "Current week", "Total"]
plot_df = display_df.drop(columns=to_drop)
plot_df.set_index("Player", inplace=True)
cumulative_plot_df = plot_df.cumsum(axis=1)
df = cumulative_plot_df.stack().reset_index()
df.rename(columns={"Player": "Names", "level_1": "Event", 0: "Score"}, inplace=True)

# plotly plotting if wanted
with st.expander("Plot points"):
    player_names = list(df["Names"].unique())
    people_to_plot = st.multiselect("Select players:", player_names, default=player_names)
    filtered_df = df[df["Names"].isin(people_to_plot)]

    cumulative_chart_plotly = px.line(filtered_df, x="Event", y="Score", color="Names", markers=True)
    st.plotly_chart(cumulative_chart_plotly)

with st.expander("Plot player position progression"):
    # bump_chart_dict = dict()
    bump_chart_df = deepcopy(cumulative_plot_df)
    cols = cumulative_plot_df.columns
    for column in cols:
        cumulative_plot_df.sort_values(by=[column], ascending=False, inplace=True)
        # bump_chart_dict[column] = pd.Series(cumulative_plot_df.index)
        bump_chart_df[column] = cumulative_plot_df.index

    bump_chart_df.index = range(1, len(cumulative_plot_df) + 1)

    bump_chart_pivot_df = bump_chart_df.reset_index()
    position = bump_chart_pivot_df["index"]

    bmp_df = pd.DataFrame()
    all_bmp_df = list()
    for column in cols:
        tmp_df = pd.concat([bump_chart_pivot_df[column], position], axis="columns")
        tmp_df.rename(columns={column: "Player", "index": "Position"}, inplace=True)
        tmp_df["Event name"] = column
        all_bmp_df.append(tmp_df)
        bmp_df = pd.concat([bmp_df, tmp_df])

    bump_chart_plotly = px.line(bmp_df, x="Event name", y="Position", color="Player", symbol="Player", markers=True)
    bump_chart_plotly.update_yaxes(autorange="reversed")
    st.plotly_chart(bump_chart_plotly)

# endregion

# region Displaying player choices
st.write("## :woman-raising-hand: Player picks :man-raising-hand:")
player_picks_df = player_picks_df[['motogp_1', 'motogp_2', 'motogp_3', 'moto2_1', 'moto2_2', 'moto2_3', 'moto3_1', 'moto3_2', 'moto3_3']]
st.dataframe(player_picks_df)
# endregion

# extra yogo
# clicked = st.button("For more Yogo, click here")
# if clicked:
#     st.image("baby_yogo.jpg", caption="Baby Yogo, before he could ride a bike", width=200)
