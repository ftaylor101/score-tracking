import streamlit as st
import os
import json
import requests
from typing import Dict, Tuple
from datetime import date, timedelta
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud.storage import Blob


# region authentication
def init_with_service_account(cred_dict: Dict):
    """
    Initialize the Firebase Storage client using a service account

    Args:
        cred_dict: dictionary with credentials

    Returns:
        storage client
    """
    cred = credentials.Certificate(cred_dict)
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credential=cred, options={
            'storageBucket': 'score-tracking-e8aeb.appspot.com'
        })
    return storage.bucket('score-tracking-e8aeb.appspot.com')


key_dict = json.loads(st.secrets["firebasetextkey"])
my_bucket = init_with_service_account(key_dict)
# endregion

# region session state setup
if "picture_start_date" not in st.session_state:
    st.session_state["picture_start_date"] = date.today() - timedelta(days=5)
if "picture_end_date" not in st.session_state:
    st.session_state["picture_end_date"] = date.today() + timedelta(days=31)
if "downloaded_pictures" not in st.session_state:
    st.session_state["downloaded_pictures"] = list()
# endregion

# region Introduction to page
st.markdown("# Share your pictures of MotoGP holidays")
st.write("This page is for us to share a few pictures of any race weekends we may go on this season.")
st.write("Choose an image and give it a name and then hit the upload button.")
st.write("To view pictures, choose the date range you wish to see pictures from and click show pictures.")
# endregion


# region helper functions
def download_image(blob: Blob, filename: str) -> str:
    """
    Function to download an image from a Google Firebase store to a local folder for static file serving.

    Args:
        blob: The Firebase blob to download.
        filename: The filename of the image, default will be the name used during storage.

    Returns:
        The path to the image including file name.
    """
    name = filename.split(".")[0]
    image_path = r"../score-tracking/static/" + name + ".jpg"
    if name not in st.session_state["downloaded_pictures"]:
        blob.download_to_filename(image_path)
        st.session_state["downloaded_pictures"].append(name)
    return image_path
# endregion


# region upload
def upload_image_to_firebase_storage(local_image_path: str, blob_name: str):
    """
    Helper function to create a new blob and to place the specified image in it.

    Args:
        local_image_path: The local name of the image to store.
        blob_name: The name of the image as will be seen in storage.
    """
    blob = my_bucket.blob(blob_name)
    blob.upload_from_filename(local_image_path)


def process_upload(image_to_upload, new_image_name: str) -> bool:
    """
    A method to prepare the image for upload and then to pass it to the upload method and verify if all happened
    successfully.

    Args:
        image_to_upload: The image to upload as a UploadedFile type.
        new_image_name: The name of the saved image.

    Return:
        Boolean describing success or not.
    """
    success = False
    local_img = image_to_upload.name
    file_available = False
    try:
        with open(local_img, "wb") as f:
            f.write(image_to_upload.getbuffer())
            file_available = True
    except:
        st.error("Something went wrong when preparing the image")

    if file_available and image_to_upload is not None:
        try:
            upload_image_to_firebase_storage(local_image_path=local_img, blob_name=new_image_name)
            success = True
            st.success('Image uploaded successfully!')
        except:
            success = False
            st.error('Image has not been uploaded, please try again.')
        finally:
            try:
                os.remove(local_img)
            except FileNotFoundError:
                pass
    return success


headers = {"Authorization": f"Bearer {st.secrets['huggingface']}"}
API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

with st.expander("Click here for photo upload"):
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    image_name = st.text_input("Image name")
    tmp_img = "temp_img"
    if uploaded_file:
        with open(tmp_img, "wb") as file_to_open:
            file_to_open.write(uploaded_file.getbuffer())
        with open(tmp_img, "rb") as file_to_read:
            img_data = file_to_read.read()
        response = requests.request("POST", API_URL, headers=headers, data=img_data)
        output = json.loads(response.content.decode("utf-8"))
        is_ice_cream = False
        for obj in output:
            if "ice cream" in obj['label']:
                is_ice_cream = True
        if is_ice_cream:
            st.write("Well done, I detect some ice cream! You can upload this.")
        else:
            st.write(f"Nice picture but no ice cream. I detect a {output[0]['label']}. But you can't upload this. It "
                     f"needs ice cream.")
    with st.form("upload_image", clear_on_submit=True):
        upload = st.form_submit_button(label="Upload")

if upload and uploaded_file and image_name and is_ice_cream:
    image_has_uploaded = process_upload(image_to_upload=uploaded_file, new_image_name=image_name)
elif upload and uploaded_file and image_name and not is_ice_cream:
    st.error("NO ICE CREAM!!!")
# endregion


# region show pictures
def show_picture_callback(date_range: Tuple[date, date]):
    """
    Callback function to update the session state with the date ranges for showing pictures.

    Args:
        date_range: A tuple selected defining the start date and end date, as datetime.date objects.
    """
    st.session_state["picture_start_date"] = date_range[0]
    st.session_state["picture_end_date"] = date_range[1]


with st.form("date_picker"):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(label="Show pictures from...")
    with col2:
        end_date = st.date_input(label="Show pictures to...")
    dates_picked = st.form_submit_button(
        label="Show pictures",
        on_click=show_picture_callback,
        args=((start_date, end_date), )
    )

if dates_picked:
    all_blobs = my_bucket.list_blobs()
    for b in all_blobs:
        if start_date < date.fromtimestamp(b.time_created.timestamp()) < end_date:
            image = download_image(blob=b, filename=b.name)
            st.image(image, caption=b.name)
# endregion
