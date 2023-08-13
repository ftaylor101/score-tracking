import streamlit as st
import json
import requests
import tensorflow as tf
import plotly.express as px
from typing import Dict
import firebase_admin
from firebase_admin import credentials, storage, ml

st.write("Page is under maintenance, I will try to get it back up as soon as possible.")
#
# # region authentication
# def init_with_service_account(cred_dict: Dict):
#     """
#     Initialize the Firebase Storage client using a service account
#
#     Args:
#         cred_dict: dictionary with credentials
#
#     Returns:
#         storage client
#     """
#     cred = credentials.Certificate(cred_dict)
#     try:
#         firebase_admin.get_app()
#     except ValueError:
#         firebase_admin.initialize_app(credential=cred, options={
#             'storageBucket': 'score-tracking-e8aeb.appspot.com'
#         })
#     return storage.bucket('score-tracking-e8aeb.appspot.com')
#
#
# key_dict = json.loads(st.secrets["firebasetextkey"])
# my_bucket = init_with_service_account(key_dict)
# # endregion
#
#
# # region helper functions
# @st.cache_resource
# def download_models():
#     predict = tf.keras.utils.get_file(
#         'style_predict.tflite',
#         "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/prediction/1?lite-format=tflite"
#     )
#     transform = tf.keras.utils.get_file(
#         'style_transform.tflite',
#         "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/transfer/1?lite-format=tflite"
#     )
#     return predict, transform
#
#
# def load_img(path_to_img) -> tf.dtypes:
#     """
#     Function to load an image from a file, and add a batch dimension.
#
#     Args:
#         path_to_img: the image
#
#     Returns:
#         A tensorflow image as dtype
#     """
#     img = tf.io.decode_image(path_to_img, channels=3)
#     img = tf.image.convert_image_dtype(img, tf.float32)
#     img = img[tf.newaxis, :]
#     return img
#
#
# def preprocess_image(image: tf.dtypes, target_dim: int) -> tf.image:
#     """
#     Function to pre-process by resizing and central cropping it.
#
#     Args:
#         image: The image to edit.
#         target_dim: The dimension to reduce the image down to.
#
#     Return:
#         The resized and cropped image.
#     """
#     # Resize the image so that the shorter dimension becomes 256px.
#     shape = tf.cast(tf.shape(image)[1:-1], tf.float32)
#     short_dim = min(shape)
#     scale = target_dim / short_dim
#     new_shape = tf.cast(shape * scale, tf.int32)
#     image = tf.image.resize(image, new_shape)
#
#     # Central crop the image.
#     image = tf.image.resize_with_crop_or_pad(image, target_dim, target_dim)
#
#     return image
#
#
# def visualise_image(image: tf.Tensor):
#     """
#     Helper function to display an image from a tensor.
#
#     Args:
#         image: The image to display.
#     """
#     img = tf.squeeze(image, axis=0)
#     fig = px.imshow(img)
#     st.plotly_chart(fig)
#
# # endregion
#
#
# # region ml functions
# def run_style_predict(image, model_path):
#     """
#     Function to run style prediction on preprocessed style image.
#
#     Args:
#         image: The preprocessed style image
#         model_path: The path to the model for predicting style.
#
#     Returns:
#         A function that can produce a tensor.
#     """
#     # Load the model.
#     interpreter = tf.lite.Interpreter(model_path=model_path)
#
#     # Set model input.
#     interpreter.allocate_tensors()
#     input_details = interpreter.get_input_details()
#     interpreter.set_tensor(input_details[0]["index"], image)
#
#     # Calculate style bottleneck.
#     interpreter.invoke()
#     bottleneck = interpreter.tensor(interpreter.get_output_details()[0]["index"])()
#
#     return bottleneck
#
#
# def run_style_transform(the_style_bottleneck, the_preprocessed_content_image, model_path):
#     """
#     Run style transform on preprocessed style image
#
#     Args:
#         the_style_bottleneck:
#         the_preprocessed_content_image:
#         model_path: The model style_transform_path
#
#     Returns:
#         sdf
#     """
#     # Load the model.
#     interpreter = tf.lite.Interpreter(model_path=model_path)
#
#     # Set model input.
#     input_details = interpreter.get_input_details()
#     interpreter.allocate_tensors()
#
#     # Set model inputs.
#     interpreter.set_tensor(input_details[0]["index"], the_preprocessed_content_image)
#     interpreter.set_tensor(input_details[1]["index"], the_style_bottleneck)
#     interpreter.invoke()
#
#     # Transform content image.
#     stylized_image = interpreter.tensor(interpreter.get_output_details()[0]["index"])()
#
#     return stylized_image
# # endregion
#
#
# st.write("# Experimental style transfer")
# st.write("Do you wish Claude Monet could have painted a picture of your cat? Or perhaps that Van Gogh had painted "
#          "your sunflowers and not his. Well wonder no more, as now you can see how your images would look like "
#          "had they been painted by someone else.")
# st.write("To use the tool below, upload a content picture, this is your picture, which will be redrawn in a new style.")
# st.write("Then upload a style picture, this is a picture that contains the style you wish to your content to look "
#          "like.")
# st.write("The blend factor defines how much of the content's original style remains in the generated picture."
#          "0% means the style picture is applied fully, 100% means most of your picture remains.")
# st.write("Or just use the defaults, which is a picture of a beach in Nice for the content and Claude Monet's "
#          "Water Lilies for the style.")
#
# style_predict_path, style_transform_path = download_models()
# # style_predict_path = tf.keras.utils.get_file(
# #     'style_predict.tflite',
# #     "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/prediction/1?lite-format=tflite"
# # )
# # style_transform_path = tf.keras.utils.get_file(
# #     'style_transform.tflite',
# #     "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/transfer/1?lite-format=tflite"
# # )
#
# # Select the images
# col1, col2 = st.columns([0.5, 0.5])
# with col1:
#     st.write("Upload image for content. If not, default beach picture is used")
#     content_file = st.file_uploader(label="Content picture", type=["jpg", "jpeg"])
#     if content_file:
#         st.image(content_file)
#         content_image = load_img(content_file.getvalue())
#     else:
#         st.image("big_beach.JPG", caption="Content")
#         img = tf.io.read_file("big_beach.JPG")
#         content_image = load_img(img)
#
# with col2:
#     st.write("Upload image for style. If not, default Claude Monet's Water Lilies is used")
#     style_file = st.file_uploader(label="Style picture", type=["jpg", "jpeg"])
#     if style_file:
#         st.image(style_file)
#         style_image = load_img(style_file.getvalue())
#     else:
#         st.image("Water-Lilies-by-Claude-Monet.jpg", caption="Style")
#         img = tf.io.read_file("Water-Lilies-by-Claude-Monet.jpg")
#         style_image = load_img(img)
#
# # Preprocess the input images.
# preprocessed_content_image = preprocess_image(content_image, 384)
# preprocessed_style_image = preprocess_image(style_image, 256)
#
# # Calculate style bottleneck for the preprocessed style image.
# style_bottleneck = run_style_predict(preprocessed_style_image, style_predict_path)
#
# # Style Blending
# # Calculate style bottleneck of the content image.
# style_bottleneck_content = run_style_predict(preprocess_image(content_image, 256), style_predict_path)
#
# with st.form(key="Blending"):
#     st.write("0 is maximum blend, 100 is minimum blend")
#     blend = st.slider("Blend ratio", min_value=0, max_value=100)
#     content_blending_ratio = blend / 100
#     submit_button = st.form_submit_button(label="Select blend")
#
# if submit_button:
#     # Blend the style bottleneck of style image and content image
#     style_bottleneck_blended = \
#         content_blending_ratio * style_bottleneck_content + (1 - content_blending_ratio) * style_bottleneck
#
#     stylized_image_blended = run_style_transform(
#         style_bottleneck_blended, preprocessed_content_image, style_transform_path
#     )
#
#     visualise_image(stylized_image_blended)
#
#
# models = [
#     "gpt2",
#     "bert-base-uncased",
#     "google/vit-base-patch16-224",
#     "facebook/bart-large-cnn"
# ]
# model_id = st.selectbox("Select model", models)
# API_URL = "https://api-inference.huggingface.co/models/" + model_id
# headers = {"Authorization": f"Bearer {st.secrets['huggingface']}"}
#
#
# def model_query(payload: str):
#     json_data = json.dumps(payload)
#     response = requests.request("POST", API_URL, headers=headers, data=json_data)
#     return json.loads(response.content.decode("utf-8"))
#
#
# with st.form(key="Huggingface"):
#     st.write("Hugging face model use")
#     st.write("This is very experimental as I am learning how to incorporate models hosted on Hugging Face into this "
#              "site and what use it can provide.")
#     query_input = st.text_input("Input query here", value="Tell me something interesting")
#     do_something = st.form_submit_button(label="Click here to do something")
#
# if do_something:
#     query_return = model_query(query_input)
#     st.write(query_return)
