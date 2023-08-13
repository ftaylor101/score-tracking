import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json
from typing import Dict
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime


col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.write("#### Welcome to Sandra's MotoGP Sweepstake")
    st.write("Points for each player are summarised in the table below, and weekly totals are plotted for those "
             "who like that sort of thing (like me)")
with col2:
    st.image("Yogo on a motorbike.jpg", caption="Yogo the yoghurt looking cool")


st.markdown("The site is **:red[undergoing maintenance]**. I will keep the points page up but it may go down "
            "temporarily if needed, and the race pace and free practice analysis will be down until I clean up the "
            "backend.")

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
        tmp_df = pd.DataFrame(data=db_doc.to_dict(), index=[db_doc.id])
        out_df = pd.concat([out_df, tmp_df])
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
score_df.sort_values(by="total", ascending=False, inplace=True)
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

# organising the dataframe
to_remove = ["bonus_30", "bonus_50"]
display_df = score_df.drop(columns=to_remove)
display_df = display_df.reindex(columns=sorted(display_df.columns))

display_df["Player"] = display_df.index
display_df.index = pd.RangeIndex(1, len(display_df.index)+1)

# Reorganise so race results are the last columns
summary_columns = \
    ["Current week Moto3", "Current week Moto2", "Current week MotoGP", "Current week", "Total", "Player"]
for col in summary_columns:
    display_df = move_column(display_df, col, 0)

# styling the dataframe
float_cols = display_df.columns[1:]  # Player name column has been set as the first column
formatted_df = display_df.style.format('{:.0f}', subset=float_cols)
formatted_df.apply(highlight_column, axis=None)

st.dataframe(formatted_df, use_container_width=True)
# endregion

# region Plotting
st.write("## :chart_with_upwards_trend: Plot :chart_with_downwards_trend:")
to_drop = ["Current week MotoGP", "Current week Moto2", "Current week Moto3", "Current week", "Total"]
plot_df = display_df.drop(columns=to_drop)
plot_df.set_index("Player", inplace=True)
cumulative_plot_df = plot_df.cumsum(axis=1)
df = cumulative_plot_df.stack().reset_index()
df.rename(columns={"Player": "Names", "level_1": "Event", 0: "Score"}, inplace=True)

# plotly plotting if wanted
# plot_checkbox = st.checkbox("Plot points")
# if plot_checkbox:
#     player_names = list(df["Names"].unique())
#     people_to_plot = st.multiselect("Select players:", player_names, default=player_names)
#     filtered_df = df[df["Names"].isin(people_to_plot)]
#
#     cumulative_chart_plotly = px.line(filtered_df, x="Event", y="Score", color="Names", markers=True)
#     st.plotly_chart(cumulative_chart_plotly)

# endregion

# region Displaying player choices
st.write("## :woman-raising-hand: Player picks :man-raising-hand:")
player_picks_df = player_picks_df[['motogp_1', 'motogp_2', 'motogp_3', 'moto2_1', 'moto2_2', 'moto2_3', 'moto3_1', 'moto3_2', 'moto3_3']]
st.dataframe(player_picks_df)
# endregion

# extra yogo
clicked = st.button("For more Yogo, click here")
if clicked:
    st.image("baby_yogo.jpg", caption="Baby Yogo, before he could ride a bike", width=200)
