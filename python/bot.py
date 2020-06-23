import os
from dotenv import load_dotenv
from fbmbot import FBMClient
load_dotenv()

token = os.getenv("DISCORD_TOKEN")

client = FBMClient()
client.run(token)