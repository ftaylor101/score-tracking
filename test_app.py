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

# Set new data
riders = ["Brad Binder", "Marc Marquez", "Enea Bastianini", "Pecco Bagnaia", "Fabio Quatararo"]
for rider in riders:
    rider_doc = db.collection("test_scores").document(rider)
    st.write(f"Setting sprint points for {rider}")
    rider_doc.update({"race3": 9})
