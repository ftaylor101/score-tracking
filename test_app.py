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

players = ["Dave", "Frederic"]
st.write("## Setting test")
player_data = db.collection("Dave")
doc_ref = player_data.list_documents()
for doc in doc_ref:
    st.write("Getting collections")
    collections = doc.collections()
    st.write("Now looping through collections")
    for collection in collections:
        st.write(f"collection id: {collection.id}")
        for collection_doc in collection.stream():
            st.write(f"{collection_doc.id} => {collection_doc.to_dict()}")
    st.write("Ended collections, now looking at player scores")
    st.write(f"doc data: {doc.id}")
    data = doc.get()
    st.write(f"current player scores for each chosen rider: {data.to_dict()}")

