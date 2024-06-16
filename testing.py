import os
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

image_path = 'screenshot.png'  # Ensure this image exists for testing
image = Image.open(image_path)
custom_config = r'--oem 3 --psm 6 -l rus'
text = pytesseract.image_to_string(image, config=custom_config)
print(text)
