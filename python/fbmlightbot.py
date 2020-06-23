import discord
import re
import tempfile
from requests_html import AsyncHTMLSession

asession = AsyncHTMLSession()

ignore = ["This listing is far from your current location.", "See listings near me"]
location_regex = re.compile("Listed (.*) in (.*)")
url_regex = re.compile("https:\/\/www.facebook\.com\/marketplace\/item\/.*")

class FBMHTMLClient(discord.Client):
    async def on_ready(self):
        print(f'{self.user} has connected.')

    async def on_message(self, message):        
        name = "N/A"
        price = "N/A"
        time = "N/A"
        location = "N/A"

        if not url_regex.match(message.content):
            return
        print("Received a FBM url")
        try:
            print("Getting URL content")
            r = await asession.get(message.content)
            print("Rendering...")
            await r.html.arender()
            print("Processing URL contents")
            count = 1
            for el in r.find("span"):
                if el.text != "" and el.text not in ignore:
                    if count == 1:
                        name = el.text
                    elif count == 2:
                        price = el.text
                    elif location_regex.match(el.text):
                        matches = location_regex.match(el.text)
                        time = matches.group(1)
                        location = matches.group(2)
                    count += 1
            if name == "N/A" and price == "N/A" and time == "N/A" and location == "N/A":
                print("Failed to parse!")
            else:
                output = "Name: {}\n".format(name)
                output += "Price: {}\n".format(price)
                output += "Listed: {}\n".format(time)
                output += "Location: {}".format(location)
                print(output)
                await message.channel.send(output)
        except Exception as error:
            print("Something went wrong")
            print(error)
            await message.channel.send("Something went wrong")