import streamlit as st
import pandas as pd
import altair as alt
import json
from typing import Dict
import firebase_admin
from firebase_admin import firestore, credentials

st.button("Want some balloons? Click here!", on_click=st.balloons)


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

# Get data and print to screen
doc_ref = db.collection("players")
score_df = pd.DataFrame()
for doc in doc_ref.stream():
    temp_df = pd.DataFrame(data=doc.to_dict(), index=[doc.id])
    score_df = pd.concat([score_df, temp_df])

st.write("## Points")
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

to_remove = ["bonus_30", "bonus_50"]
display_df = score_df.drop(columns=to_remove)
display_df = display_df.reindex(columns=sorted(display_df.columns))
st.dataframe(display_df, use_container_width=True)

st.write("## Plot")
to_drop = ["Current week MotoGP", "Current week Moto2", "Current week Moto3", "Current week", "Total"]
plot_df = display_df.drop(columns=to_drop)
cumulative_plot_df = plot_df.cumsum(axis=1)
df = cumulative_plot_df.stack().reset_index()
df.rename(columns={"level_0": "Names", "level_1": "Event", 0: "Score"}, inplace=True)

# altair plotting if wanted
plot_checkbox = st.checkbox("Plot points")
if plot_checkbox:
    player_names = list(df["Names"].unique())
    people_to_plot = st.multiselect("Select players:", player_names, default=player_names)
    filtered_df = df[df["Names"].isin(people_to_plot)]
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['Event'], empty='none')
    # The basic line
    line = alt.Chart(filtered_df).mark_line(
        point=alt.OverlayMarkDef()
    ).encode(
        x='Event:N',
        y='Score:Q',
        color='Names:N'
    )
    # Transparent selectors across the chart. This is what tells us the x-value of the cursor
    selectors = alt.Chart(filtered_df).mark_point().encode(
        x='Event:N',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )
    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )
    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'Score:Q', alt.value(' '))
    )
    # Draw a rule at the location of the selection
    rules = alt.Chart(filtered_df).mark_rule(color='gray').encode(
        x='Event:N',
    ).transform_filter(
        nearest
    )
    # Put the five layers into a chart and bind the data
    cht = alt.layer(
        line, selectors, points, rules, text
    ).properties(
        width=600, height=300
    )
    st.altair_chart(cht, use_container_width=True)

st.write("## Player picks")
doc_ref = db.collection("picks")
# Get player picks and print to screen
player_picks_df = pd.DataFrame()
for doc in doc_ref.stream():
    tmp_dct = {k: [v] for k, v in doc.to_dict().items()}
    player_picks_df = pd.concat([player_picks_df, pd.DataFrame(tmp_dct, index=[doc.id])])

player_picks_df = player_picks_df[['motogp_1', 'motogp_2', 'motogp_3', 'moto2_1', 'moto2_2', 'moto2_3', 'moto3_1', 'moto3_2', 'moto3_3']]
st.dataframe(player_picks_df)
