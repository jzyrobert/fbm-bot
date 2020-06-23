import discord
import atexit
import re
import tempfile
from selenium import webdriver

ignore = ["This listing is far from your current location.", "See listings near me","›"]
location_regex = re.compile("Listed (.*) in (.*)")
url_regex = re.compile("https:\/\/www.facebook\.com\/marketplace\/item\/.*")

def exit_handler(client):
    if client.driver:
        client.driver.quit()

class FBMClient(discord.Client):
    async def on_ready(self):
        print(f'{self.user} has connected.')
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)
        atexit.register(exit_handler, self)

    async def on_message(self, message):        
        name = "N/A"
        price = "N/A"
        time = "N/A"
        location = "N/A"

        if not url_regex.match(message.content):
            return
        print("Received a FBM url")
        try:
            self.driver.get(message.content)
            print("Processing URL contents")
            elementsFound = self.driver.find_elements_by_tag_name("span")
            for i in range(len(elementsFound)):
                el = elementsFound[i]
                if el.text != "":
                    print(el.text)
                if location_regex.match(el.text):
                    matches = location_regex.match(el.text)
                    time = matches.group(1)
                    location = matches.group(2)
                    # go in reverse
                    count = 0
                    j = i
                    while j >= 0 and count < 2:
                        j -= 1
                        el = elementsFound[j]
                        if el.text != "" and el.text not in ignore:
                            if count == 0:
                                price = el.text
                            else:
                                name = el.text
                            count += 1
                    break
            if name == "N/A" and price == "N/A" and time == "N/A" and location == "N/A":
                print("Something went wrong")
            else:
                output = "Name: {}\n".format(name)
                output += "Price: {}\n".format(price)
                output += "Listed: {}\n".format(time)
                output += "Location: {}".format(location)
                print(output)
                await message.channel.send(output)
        except Exception as e:
            print("Something went wrong")
            print(e)