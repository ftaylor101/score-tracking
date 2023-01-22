import streamlit as st
from google.cloud import firestore


# Authenticate
db = firestore.Client.from_service_account_json("firestore-key.json")

# Create a reference to the collection
st.write("## Rider scores")
doc_ref = db.collection("test_scores")

# Get data and print to screen
for doc in doc_ref.stream():
    st.write(f"{doc.id} has details: {doc.to_dict()} points")


st.write("## Player picks")
doc_ref = db.collection("Picks")

# Get data and print to screen
for doc in doc_ref.stream():
    st.write(f"{doc.id} has picked: {doc.to_dict()}")


st.write("## Player scores")
doc_ref = db.collection("Players")

# Get data and print to screen
for doc in doc_ref.stream():
    st.write(f"{doc.id} has scored: {doc.to_dict()} points")

# # Create new test_score document
# doc_ref = db.collection("test_scores").document("player3_scores")
# doc_ref.set({
#     "rider1_mgp": "Rossi",
#     "rider2_mgp": "Bossi",
#     "rider3_mgp": "Messi",
#     "bonus30_mgp": 0
# })
