import discord
import atexit
import re
import tempfile
from selenium import webdriver

ignore = ["This listing is far from your current location.", "See listings near me"]
location_regex = re.compile("Listed (.*) in (.*)")
url_regex = re.compile("https:\/\/www.facebook\.com\/marketplace\/item\/.*")

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

def exit_handler():
    driver.quit()

atexit.register(exit_handler)

class FBMClient(discord.Client):
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
        driver.get(message.content)
        print("Processing URL contents")
        count = 1
        for el in driver.find_elements_by_tag_name("span"):
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
            print("Something went wrong")
            print(driver.page_source)
            log = tempfile.TemporaryFile()
            log.write(driver.page_source)
            await message.channel.send("Something went wrong, attaching log", file=discord.File(log, filename="log.txt"))
        else:
            output = "Name: {}\n".format(name)
            output += "Price: {}\n".format(price)
            output += "Listed: {}\n".format(time)
            output += "Location: {}".format(location)
            print(output)
            await message.channel.send(output)