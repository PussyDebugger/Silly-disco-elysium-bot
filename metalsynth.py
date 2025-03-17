import random
import os
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

# Handling tokens via .env file
load_dotenv(dotenv_path="tokens.env")

telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_username = os.getenv("TELEGRAM_USERNAME")

gemini_token = os.getenv("GEMINI_TOKEN")
client = genai.Client(api_key=gemini_token)

response_weight = 0.05

# Generating response using gemini 
def respond(text: str) -> str:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read().format(text=text)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text

# Handling text message
async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    # Skips random messages with response_weight chance, where 0 is skip all and 1 is don't skip any
    if random.random() > response_weight:
        print("Message skipped.")
        return
    reply = respond(message).strip()
    print("Message ready.")
    print(f"{message} :: {reply}")
    await update.message.reply_text(reply)

# Handling image message
async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image = await update.message.photo[-1].get_file()
    image_path = image.file_path
    photo = requests.get(image_path)

    with open("prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read().format(text="Image")
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[f"{prompt}", types.Part.from_bytes(data=photo.content, mime_type="image/jpeg")])
    await update.message.reply_text(response.text)

# Doesn't do anything
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return(f"{update}:::::{context.error}")

# Forces response with /generate <MESSAGE> command
async def generate_command(update: Update, context: CallbackContext):
    message_text = " ".join(context.args)
    reply = respond(message_text)
    await update.message.reply_text(reply)

# Sets response_weight via /weight <CHANCE> command
async def weight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global response_weight
    response_weight = float(context.args[0])
    await update.message.reply_text(f"Weight set to {response_weight}")

if __name__ == "__main__":
    app = Application.builder().token(telegram_token).build()

    # Handlers to trigger command functions
    app.add_handler(CommandHandler('generate', generate_command))
    app.add_handler(CommandHandler('weight', weight_command))

    # Handlers to trigger message functions
    app.add_handler(MessageHandler(filters.TEXT, get_message))
    app.add_handler(MessageHandler(filters.PHOTO, get_image))

    app.add_error_handler(error)
    print("Polling")

    # Looks for new messages in chat/group with interval in seconds
    app.run_polling(poll_interval=5)