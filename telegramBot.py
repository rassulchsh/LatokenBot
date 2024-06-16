import os
import json
import logging
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the OpenAI API client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load cleaned extracted text data
with open('cleaned_extracted_text.json', 'r') as json_file:
    cleaned_data = json.load(json_file)

# Prepare the data for retrieval
documents = []
for key in cleaned_data:
    documents.extend(cleaned_data[key])

# Load a pre-trained sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode the documents to create a document embedding index
doc_embeddings = model.encode(documents, convert_to_tensor=True).cpu().detach().numpy()

# Create a FAISS index
index = faiss.IndexFlatL2(doc_embeddings.shape[1])
index.add(doc_embeddings)

# Initialize the conversation history
conversation_history = []

# Define command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, друган {user.mention_markdown_v2()}\! Я твой помощник по хакатону LATOKEN\. Задавай любые вопросы о LATOKEN или хакатоне\!',
        reply_markup=ForceReply(selective=True),
    )
    # Clear conversation history
    conversation_history.clear()

# Define command handler for the /reset command
def reset(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Чат был очищен. Начнем сначала! Задайте ваш вопрос.')
    # Clear conversation history
    conversation_history.clear()

# Define function to handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    conversation_history.append({"role": "user", "content": user_message})
    response = generate_response(conversation_history)
    update.message.reply_text(response)
    conversation_history.append({"role": "assistant", "content": response})

# Define function to generate responses using OpenAI in Russian
def generate_response(history):
    try:
        # Retrieve the most relevant documents based on the latest user message
        query_embedding = model.encode([history[-1]["content"]], convert_to_tensor=True).cpu().detach().numpy()
        _, indices = index.search(query_embedding, k=5)
        relevant_docs = [documents[idx] for idx in indices[0]]
        context_data = ' '.join(relevant_docs)

        # Create the prompt for OpenAI with the conversation history
        messages = [
            {"role": "system", "content": f"Ты полезный помощник, знающий о Latoken и его хакатоне. Вот некоторая информация: {context_data}"},
        ] + history

        # Generate the response using the latest OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5
        )

        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Извините, сейчас я испытываю трудности с пониманием. Пожалуйста, попробуйте позже."

# Define main function to start the bot
def main() -> None:
    # Get the Telegram token from environment variables
    token = os.getenv("TELEGRAM_TOKEN")

    if not token:
        logger.error("No TELEGRAM_TOKEN found in environment variables")
        return

    # Create the Updater and pass it your bot's token
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("reset", reset))

    # Register message handler for general messages
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
