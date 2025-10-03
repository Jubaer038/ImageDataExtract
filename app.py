import streamlit as st
import cv2
import pytesseract
from PIL import Image
import requests
import numpy as np
import shutil
import os
import re

# -------------------------------
# Configure Tesseract Path
# -------------------------------
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(win_path):
        pytesseract.pytesseract.tesseract_cmd = win_path
    else:
        st.error("Tesseract OCR not found! Please install it.")
        st.stop()

# -------------------------------
# Page Settings
# -------------------------------
st.set_page_config(page_title="Image Data Extract & Compare", layout="wide")
st.title("📷 Image Data Extract & Compare")
st.write("Upload an image OR take a photo, extract temperature text, and compare with OpenWeather API.")

# -------------------------------
# Initialize session state
# -------------------------------
if "image_file" not in st.session_state:
    st.session_state.image_file = None
if "extracted_temp" not in st.session_state:
    st.session_state.extracted_temp = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "current_source" not in st.session_state:
    st.session_state.current_source = None
if "open_camera" not in st.session_state:
    st.session_state.open_camera = False

# -------------------------------
# Tabs: Upload / Camera
# -------------------------------
tab1, tab2 = st.tabs(["📤 Upload Image", "📸 Take Photo"])

# --- Upload Tab ---
with tab1:
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        # Reset state if new image
        if st.session_state.current_source != "upload" or st.session_state.image_file != uploaded_file:
            st.session_state.image_file = uploaded_file
            st.session_state.extracted_temp = None
            st.session_state.extracted_text = ""
            st.session_state.current_source = "upload"

# --- Camera Tab ---
with tab2:
    if not st.session_state.open_camera:
        if st.button("📸 Open Camera"):
            st.session_state.open_camera = True
    else:
        st.info("Take a photo below 👇")
        camera_file = st.camera_input("Take a photo")

        if camera_file is not None:
            # Reset state if new photo
            if st.session_state.current_source != "camera" or st.session_state.image_file != camera_file:
                st.session_state.image_file = camera_file
                st.session_state.extracted_temp = None
                st.session_state.extracted_text = ""
                st.session_state.current_source = "camera"

# -------------------------------
# OCR Extraction
# -------------------------------
if st.session_state.image_file is not None:
    try:
        image = Image.open(st.session_state.image_file).convert("RGB")
        img_array = np.array(image)
        st.image(image, caption="Selected Image", use_column_width=True)

        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        extracted_text = pytesseract.image_to_string(gray)
        st.session_state.extracted_text = extracted_text

        st.subheader("📝 Extracted Text")
        st.text(st.session_state.extracted_text)

        temp_matches = re.findall(r'(\d+)\s*(?:°|°C|degree|degrees)', st.session_state.extracted_text, flags=re.IGNORECASE)
        if temp_matches:
            st.session_state.extracted_temp = int(temp_matches[0])
        else:
            st.session_state.extracted_temp = None

    except Exception as e:
        st.error(f"Image processing failed: {e}")

# -------------------------------
# API Compare + Card View
# -------------------------------
city = st.text_input("Enter city name for weather check", "Dhaka")

if st.button("Compare with API"):
    if st.session_state.extracted_temp is None:
        st.error("❌ No temperature value detected in image. Cannot compare with API.")
    else:
        api_key = "22f9ea86b3c7d79c4a1df5b7a06da497"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)
            data = response.json()

            if data.get("main"):
                api_temp = round(data["main"]["temp"])

                # Card-like view
                st.markdown("### 🌤 Temperature Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Extracted Temp", value=f"{st.session_state.extracted_temp}°C")
                with col2:
                    st.metric(label=f"{city} API Temp", value=f"{api_temp}°C")

                # Match / Not Match
                if st.session_state.extracted_temp == api_temp:
                    st.success("✅ Match! Extracted temperature matches API data.")
                else:
                    st.error("❌ Not Match! Extracted temperature does not match API data.")
            else:
                st.error("City not found or API error.")
        except Exception as e:
            st.error(f"API request failed: {e}")
