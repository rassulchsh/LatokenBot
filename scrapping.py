import os
import json
import time
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import hashlib

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Set TESSDATA_PREFIX to the local tessdata directory
project_path = os.path.dirname(os.path.abspath(__file__))
tessdata_dir = os.path.join(project_path, 'tessdata')
os.environ['TESSDATA_PREFIX'] = tessdata_dir

# Debugging: Print environment variables and paths
print("TESSDATA_PREFIX:", os.environ['TESSDATA_PREFIX'])
print("Tesseract CMD:", pytesseract.pytesseract.tesseract_cmd)


def setup_driver():
    # Initialize WebDriver with ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_next_slide_number(directory, prefix='screenshot_'):
    existing_files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.png')]
    if not existing_files:
        return 1
    existing_numbers = [int(f[len(prefix):-4]) for f in existing_files]
    return max(existing_numbers) + 1


def capture_and_process_slides(url, json_filename, screenshot_dir, label):
    driver = setup_driver()
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)  # Adjust this based on the loading time of the presentation

    slide_number = get_next_slide_number(screenshot_dir, prefix=f'screenshot_{label}_')
    last_hash = None

    while True:
        try:
            # Capture screenshot of the current slide
            screenshot_path = os.path.join(screenshot_dir, f'screenshot_{label}_{slide_number}.png')
            driver.save_screenshot(screenshot_path)

            # Generate hash of the screenshot to detect changes
            with open(screenshot_path, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()

            if current_hash == last_hash:
                print("No more slides or duplicate slide detected.")
                os.remove(screenshot_path)  # Clean up duplicate slide screenshot
                break

            last_hash = current_hash

            # Preprocess and extract text from the screenshot
            preprocessed_image = preprocess_image(screenshot_path)
            extracted_text = extract_text_from_image(preprocessed_image)

            # Append the extracted text to the JSON file
            append_text_to_json(extracted_text, json_filename, label)

            # Try to navigate to the next slide
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Next']"))
            )
            next_button.click()
            time.sleep(2)  # Wait for the next slide to load
            slide_number += 1
        except Exception as e:
            print(f"No more slides or an error occurred on slide {slide_number}: {e}")
            break

    driver.quit()


def preprocess_image(image_path):
    # Open the image using PIL
    image = Image.open(image_path)

    # Convert the image to grayscale
    image = image.convert('L')

    # Enhance the image contrast
    image = ImageEnhance.Contrast(image).enhance(2)
    image = image.filter(ImageFilter.MedianFilter())

    # Apply a threshold to get a binary image
    threshold = 140
    image = image.point(lambda x: 0 if x < threshold else 255, '1')

    # Resize the image to increase DPI
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)

    # Save the preprocessed image for debugging purposes (optional)
    preprocessed_image_path = 'preprocessed_' + os.path.basename(image_path)
    image.save(preprocessed_image_path)

    return image


def extract_text_from_image(image):
    # Perform OCR on the preprocessed image using pytesseract
    # Specify both Russian and English languages
    custom_config = f'--oem 3 --psm 6 -l rus+eng --tessdata-dir "{tessdata_dir}"'
    print("Custom Config:", custom_config)
    text = pytesseract.image_to_string(image, config=custom_config)
    return text


def append_text_to_json(text, filename, label):
    # Load existing data from the JSON file
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    # Append the new text under the specified label
    if label not in data:
        data[label] = []
    data[label].append(text)

    # Save the updated data to the JSON file
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


# URLs for LATOKEN Info and Hackathon Info
latoken_info_url = 'https://deliver.latoken.com/about'
hackathon_info_url = 'https://deliver.latoken.com/hackathon'

json_filename = 'extracted_text.json'
screenshot_dir = 'screenshots'

# Create the screenshot directory if it does not exist
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)

# Capture and process LATOKEN Info slides
capture_and_process_slides(latoken_info_url, json_filename, screenshot_dir, 'latoken_info')

# Capture and process Hackathon Info slides
capture_and_process_slides(hackathon_info_url, json_filename, screenshot_dir, 'hackathon_info')

print(f"Extracted text has been saved to {json_filename}")
