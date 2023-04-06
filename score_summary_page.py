import streamlit as st
import pandas as pd
import altair as alt
import json
from typing import Dict
import firebase_admin
from firebase_admin import firestore, credentials

col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.write("#### Welcome to Sandra's MotoGP Sweepstake")
    st.write("Points for each player are summarised in the table below, and weekly totals are plotted for those "
             "who like that sort of thing (like me)")
with col2:
    st.image("Yogo on a motorbike.jpg", caption="Yogo the yoghurt looking cool")


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


# region helper functions
def highlight_column(x: pd.DataFrame):
    """Highlight a particular column of a dataframe."""
    r = f"background-color: #ff9999"
    tmp_df = pd.DataFrame('', index=x.index, columns=x.columns)
    tmp_df.loc[:, "Total"] = r
    return tmp_df


def show_points():
    """
    Function to collate points and format the dataframe for visual purposes.
    """
    # todo place code in here to get data and format the dataframe
    pass


def move_column(dataframe: pd.DataFrame, column_name: str, new_position: int) -> pd.DataFrame:
    """
    Helper function to move a column to a specified location in a dataframe.

    :param dataframe: The dataframe in which to move the column.
    :param column_name: The column name.
    :param new_position: The new column index.
    :return: The dataframe with the columns rearranged.
    """
    col_to_move = dataframe.pop(column_name)
    dataframe.insert(new_position, column_name, col_to_move)
    return dataframe

# endregion


# Get data and print to screen
doc_ref = db.collection("players")
score_df = pd.DataFrame()
for doc in doc_ref.stream():
    temp_df = pd.DataFrame(data=doc.to_dict(), index=[doc.id])
    score_df = pd.concat([score_df, temp_df])

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

# Plotting
st.write("## :chart_with_upwards_trend: Plot :chart_with_downwards_trend:")
to_drop = ["Current week MotoGP", "Current week Moto2", "Current week Moto3", "Current week", "Total"]
plot_df = display_df.drop(columns=to_drop)
plot_df.set_index("Player", inplace=True)
cumulative_plot_df = plot_df.cumsum(axis=1)
df = cumulative_plot_df.stack().reset_index()
df.rename(columns={"Player": "Names", "level_1": "Event", 0: "Score"}, inplace=True)

# altair plotting if wanted
plot_checkbox = st.checkbox("Plot points")
if plot_checkbox:
    player_names = list(df["Names"].unique())
    people_to_plot = st.multiselect("Select players:", player_names, default=player_names)
    filtered_df = df[df["Names"].isin(people_to_plot)]

    # Plotting
    highlight = alt.selection(type='single', on='mouseover',
                              fields=['Names'], nearest=True)

    base = alt.Chart(filtered_df).encode(
        x='Event:O',
        y='Score:Q',
        color='Names:N'
    )

    points = base.mark_circle().encode(
        opacity=alt.value(0)
    ).add_selection(
        highlight
    ).properties(
        width=600
    )

    lines = base.mark_line().encode(
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    cht = alt.layer(points + lines).resolve_scale()
    st.altair_chart(cht, use_container_width=True)

# Displaying player choices
st.write("## :woman-raising-hand: Player picks :man-raising-hand:")
doc_ref = db.collection("picks")
# Get player picks and print to screen
player_picks_df = pd.DataFrame()
for doc in doc_ref.stream():
    tmp_dct = {k: [v] for k, v in doc.to_dict().items()}
    player_picks_df = pd.concat([player_picks_df, pd.DataFrame(tmp_dct, index=[doc.id])])

player_picks_df = player_picks_df[['motogp_1', 'motogp_2', 'motogp_3', 'moto2_1', 'moto2_2', 'moto2_3', 'moto3_1', 'moto3_2', 'moto3_3']]
st.dataframe(player_picks_df)

# extra yogo
clicked = st.button("For more Yogo, click here")
if clicked:
    st.image("baby_yogo.jpg", caption="Baby Yogo, before he could ride a bike", width=200)
