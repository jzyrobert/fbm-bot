import os
from dotenv import load_dotenv
from fbmbot import FBMClient
from fbmlightbot import FBMHTMLClient
load_dotenv()

token = os.getenv("DISCORD_TOKEN")

client = FBMClient()
# client = FBMHTMLClient()
client.run(token)