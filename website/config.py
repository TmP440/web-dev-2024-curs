from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

SECRET_KEY = os.environ["SECRET_KEY"]
DB_PASSWORD = os.environ["DATABASE__PASSWORD"]
DB_USER = os.environ["DATABASE__USER"]
DB_HOST = os.environ["DATABASE__HOST"]
DB_NAME = os.environ["DATABASE__NAME"]
DB_PORT = os.environ["DATABASE__PORT"]
