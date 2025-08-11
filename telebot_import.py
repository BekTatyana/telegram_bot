from dotenv import load_dotenv
import telebot
import os

load_dotenv()
bot = telebot.TeleBot(os.getenv("token"))
