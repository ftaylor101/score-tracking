import streamlit as st
import pandas as pd
from google.cloud import firestore

st.button("Want some balloons? Click here!", on_click=st.balloons)

# Authenticate
db = firestore.Client.from_service_account_json("firestore-key.json")

doc_ref = db.collection("players")

# Get data and print to screen
week_score = list()
total_score = list()
player_names = list()
for doc in doc_ref.stream():
    player_names.append(doc.id)
    week_score.append(doc.to_dict()["current_week"])
    total_score.append(doc.to_dict()["total"])
    # st.write(f"{doc.id} has picked: {[(k, v) for k, v in doc.to_dict().items()]}")

week_df = pd.DataFrame({"Player": player_names, "Weekly score": week_score})
total_df = pd.DataFrame({"Player": player_names, "Total score": total_score})

st.write("## Current week")
st.table(week_df)

st.write("## Total")
st.table(total_df)
