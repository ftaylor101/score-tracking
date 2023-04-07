import streamlit as st
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, storage


# region authentication
def init_with_service_account():
    """
    Initialize the Firebase Storage client using a service account

    Returns:
        storage client
    """
    cred = credentials.Certificate('score-tracking-e8aeb-b28cdfe518b4.json')
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credential=cred, options={
            'storageBucket': 'score-tracking-e8aeb.appspot.com'
        })
    return storage.bucket('score-tracking-e8aeb.appspot.com')


my_bucket = init_with_service_account()

# Page code
st.markdown("# :red[!!! WARNING !!!]")
st.write("Page under development - any pictures uploaded may be deleted without notice while I learn to do things")


# endregion


# region upload
def upload_image_to_firebase_storage(local_image_path: str, blob_name: str):
    """
    Helper function to create a new blob and to place the specified image in it.

    :param local_image_path: The local name of the image to store.
    :param blob_name: The name of the image as will be seen in storage.
    """
    print(f"Getting file {local_image_path} and saving it to {blob_name}")
    blob = my_bucket.blob(blob_name)
    blob.upload_from_filename(local_image_path)
    print("File saved")


def process_upload(image_to_upload, new_image_name: str) -> bool:
    """
    A method to prepare the image for upload and then to pass it to the upload method and verify if all happened
    successfully.

    :param image_to_upload: The image to upload as a UploadedFile type.
    :param new_image_name: The name of the saved image.

    :return: Boolean describing success or not.
    """
    success = False
    local_img = image_to_upload.name
    print(f"Local img name: {local_img}")
    print(f"new image name: {new_image_name}")
    file_available = False
    try:
        print(f"About to write open for {local_img}")
        with open(local_img, "wb") as f:
            print("Now in with")
            f.write(image_to_upload.getbuffer())
            print("Ending with")
            file_available = True
            print(f"Written file {local_img}")
            print(f"File available is {file_available}")
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
                print(f"Going to delete: {local_img}")
                os.remove(local_img)
                print("Delete should have worked if you see me")
            except FileNotFoundError:
                pass
    return success


with st.form("upload_image", clear_on_submit=True):
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    image_name = st.text_input("Image name")
    upload = st.form_submit_button(label="Upload")

if upload and uploaded_file and image_name:
    image_has_uploaded = process_upload(image_to_upload=uploaded_file, new_image_name=image_name)


# endregion


# region show pictures
with st.form("date_selection"):
    start_time = st.slider(
        label="Show pictures between the following dates",
        min_value=datetime(2023, 1, 1),
        max_value=datetime(2023, 12, 31),
        value=(datetime(2023, 2, 2), datetime(2023, 8, 8)),
        format="DD/MM/YY")
    dates_picked = st.form_submit_button(label="Show pictures")

if dates_picked:
    all_blobs = my_bucket.list_blobs()
    for b in all_blobs:
        if start_time[0].timestamp() < b.time_created.timestamp() < start_time[1].timestamp():
            st.write(b.name)
            b.download_to_filename("tmp_img.jpg")
            st.image("tmp_img.jpg")
# endregion


# @st.cache(ttl=600)
# def read_file(bucket_name, file_path):
#     bucket = client.bucket(bucket_name)
#     picture = bucket.blob(file_path).download_as_string().decode("utf-8")
#     return picture
#
# bucket_name = "test_pictures"


# st.write(my_bucket.list_blobs())
# st.write(my_bucket.blob(file_name))
# with open(dest_file_name, "w") as to_dl:
#     my_bucket.blob(file_name).download_to_file(to_dl)
# content = None
