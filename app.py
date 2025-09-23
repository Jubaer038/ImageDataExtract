import streamlit as st
import cv2
import pytesseract
from PIL import Image
import requests
import numpy as np
import shutil
import os

# -------------------------------
# Configure Tesseract Path
# -------------------------------
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    # If running on Windows, update path below after installing Tesseract
    win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(win_path):
        pytesseract.pytesseract.tesseract_cmd = win_path
    else:
        st.error("Tesseract OCR not found! Please install it.")
        st.stop()

# -------------------------------
# Streamlit Page Settings
# -------------------------------
st.set_page_config(page_title="Image Data Extract & Compare", layout="wide")
st.title("Image Data Extract & Compare")
st.write("Upload an image, extract temperature text, and compare with OpenWeather API.")

# -------------------------------
# Step 1: File Upload
# -------------------------------
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert uploaded image to OpenCV format
    image = Image.open(uploaded_file).convert("RGB")  # Ensure RGB
    img_array = np.array(image)

    st.image(image, caption="Uploaded Image", use_column_width=True)

    # -------------------------------
    # Step 2: OCR Extraction
    # -------------------------------
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)  # Convert RGB → Gray
    extracted_text = pytesseract.image_to_string(gray)

    st.subheader("Extracted Text")
    st.text(extracted_text)

    # Detect first integer (temperature-like value)
    extracted_temp = None
    for word in extracted_text.split():
        try:
            extracted_temp = int(word)
            break
        except:
            continue

    if extracted_temp is not None:
        st.success(f"Extracted Temperature: {extracted_temp}°C")
    else:
        st.warning("No temperature value detected.")

    # -------------------------------
    # Step 3: OpenWeather API
    # -------------------------------
    city = st.text_input("Enter city name for weather check", "Dhaka")

    if st.button("Compare with API"):
        #Hard-coded API key
        api_key = "22f9ea86b3c7d79c4a1df5b7a06da497"

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)
            data = response.json()

            if data.get("main"):
                api_temp = round(data["main"]["temp"])
                st.info(f"🌤 Current API Temperature in {city}: {api_temp}°C")

                if extracted_temp is not None:
                    if extracted_temp == api_temp:
                        st.success("Match! Extracted temperature matches API data.")
                    else:
                        st.error("Not Match! Extracted temperature does not match API data.")
            else:
                st.error("City not found or API error.")
        except Exception as e:
            st.error(f"API request failed: {e}")
