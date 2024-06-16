import json
import re


# Function to clean the extracted text
def clean_text(text):
    # Remove unnecessary whitespace and special characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
    text = re.sub(r'[^\w\s.,!?]', '', text)  # Remove special characters except punctuation
    text = text.strip()  # Remove leading and trailing whitespace
    return text


# Load the extracted JSON data
with open('extracted_text.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Clean the extracted text for each label
cleaned_data = {}
for label, texts in data.items():
    cleaned_data[label] = [clean_text(text) for text in texts]

# Save the cleaned data to a new JSON file
cleaned_json_filename = 'cleaned_extracted_text.json'
with open(cleaned_json_filename, 'w', encoding='utf-8') as json_file:
    json.dump(cleaned_data, json_file, ensure_ascii=False, indent=4)

print(f"Cleaned text has been saved to {cleaned_json_filename}")


# Function to extract relevant sections or information from cleaned text
def extract_relevant_info(cleaned_data):
    relevant_info = {}

    for label, texts in cleaned_data.items():
        label_info = []
        for text in texts:
            # Example extraction: Extract bullet points or sentences containing specific keywords
            points = re.findall(r'([A-Z][^.!?]*[.!?])', text)
            label_info.extend(points)

        relevant_info[label] = label_info

    return relevant_info


# Extract relevant information from cleaned data
relevant_info = extract_relevant_info(cleaned_data)

# Save the relevant information to a new JSON file
relevant_info_json_filename = 'relevant_info.json'
with open(relevant_info_json_filename, 'w', encoding='utf-8') as json_file:
    json.dump(relevant_info, json_file, ensure_ascii=False, indent=4)

print(f"Relevant information has been saved to {relevant_info_json_filename}")
