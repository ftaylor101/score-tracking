import streamlit as st
import pandas as pd
import altair as alt
from google.cloud import firestore

st.button("Want some balloons? Click here!", on_click=st.balloons)

# Authenticate
db = firestore.Client.from_service_account_json("firestore-key.json")

doc_ref = db.collection("players")

# Get data and print to screen
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
cumulative_plot_df = cumulative_plot_df.T
st.line_chart(cumulative_plot_df)

cht = alt.Chart(cumulative_plot_df).transform_fold(
    ['race_1', 'race_2', 'race_3', 'race_4', 'race_5', 'race_6'],
).mark_line().encode(
    x='Names:N',
    y='value:Q',
    color='key:N'
)

st.altair_chart(cht, use_container_width=True)
