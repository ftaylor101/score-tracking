import streamlit as st
from google.cloud import firestore


# Authenticate
db = firestore.Client.from_service_account_json("firestore-key.json")

# Create a reference to the collection
doc_ref = db.collection("test_scores")

# Get the data
# doc = doc_ref.get()

st.write("## Query test")
# print to screen
for doc in doc_ref.stream():
    # st.write("The id is: ", doc.id)
    doc_dict = doc.to_dict()
    if "sprint1" in doc_dict.keys():
        if doc_dict["sprint1"] > 10:
            st.write(f"{doc.id} scored {doc_dict['sprint1']} points")

# # Create new test_score document
# doc_ref = db.collection("test_scores").document("player3_scores")
# doc_ref.set({
#     "rider1_mgp": "Rossi",
#     "rider2_mgp": "Bossi",
#     "rider3_mgp": "Messi",
#     "bonus30_mgp": 0
# })

st.write("## Setting test")
players_ref = db.collection_group("Frederic")
for pick in players_ref.stream():
    st.write(pick.id)
    st.write(pick.to_dict())
