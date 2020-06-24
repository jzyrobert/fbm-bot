import discord
import asyncio
import atexit
import re
import tempfile
from selenium import webdriver

ignore = ["This listing is far from your current location.", "See listings near me","›"]
location_regex = re.compile("Listed (.*) in (.*)")
url_regex = re.compile("https:\/\/www.facebook\.com\/marketplace\/item\/.*")

retries = 2
minimumElements = 20
TEST_SERVER_ID = 725034603001413703

def exit_handler(client):
    if client.driver:
        client.driver.quit()

class FBMClient(discord.Client):
    def find_spans_retry(self, url):
        tries = 0
        while tries < retries:
            self.driver.get(url)
            print("Processing URL contents")
            el = self.driver.find_elements_by_tag_name("span")
            if len(el) > minimumElements:
                return el
            else:
                print("Found only {} elements, retrying..".format(len(el)))
            tries += 1
        return el
    
    def find_image_try(self):
        images = self.driver.find_elements_by_tag_name("img")
        if len(images) > 0:
            return images[0].get_attribute('src')
        return ""


    async def send_exception(self, message, content):
        if message.guild and message.guild.id == TEST_SERVER_ID:
            temp = tempfile.TemporaryFile()
            temp.write(str.encode(str(content)))
            temp.seek(0)
            await message.channel.send("Something went wrong, attaching log...",file=discord.File(temp, filename="log.txt"))
            temp.close()
    
    async def send_embed(self, message, name, price, time, location, imageurl):
        embed = discord.Embed(colour=0x3577E5)
        embed.set_author(name=name)
        embed.add_field(name="Price",value=price,inline=True)
        embed.add_field(name="Listed",value=time,inline=True)
        embed.add_field(name="Location",value=location,inline=True)
        if imageurl != "":
            embed.set_thumbnail(url=imageurl)
        await message.channel.send(embed=embed)

    async def on_ready(self):
        print(f'{self.user} has connected.')
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)
        atexit.register(exit_handler, self)
        self.lock = asyncio.Lock()

    async def on_message(self, message):        
        name = "N/A"
        price = "N/A"
        time = "N/A"
        location = "N/A"

        if not url_regex.match(message.content):
            return
        if message.guild:
            print("Received a FBM url from server {}, channel {}, user {}".format(message.guild.id, message.channel.id, message.author.name))
        else:
            print("Received a FBM url in private message from {}".format(message.author.name))
        await self.lock.acquire()
        try:
            elementsFound = self.find_spans_retry(message.content)
            print("Found {} spans".format(len(elementsFound)))
            for i in range(len(elementsFound)):
                el = elementsFound[i]
                if location_regex.match(el.text):
                    matches = location_regex.match(el.text)
                    time = matches.group(1)
                    location = matches.group(2)
                    # go in reverse
                    j = i
                    while j >= 1:
                        j -= 1
                        el = elementsFound[j]
                        if el.text not in ignore and el.text.startswith("£"):
                            price = el.text
                            name = elementsFound[j-1].text
                    break
            if name == "N/A" and price == "N/A" and time == "N/A" and location == "N/A":
                print("Something went wrong")
                await self.send_exception(message, self.driver.page_source)
            else:
                output = "Name: {}\n".format(name)
                output += "Price: {}\n".format(price)
                output += "Listed: {}\n".format(time)
                output += "Location: {}".format(location)
                print(output)
                # acquire the image
                src = self.find_image_try()
                await self.send_embed(message, name, price, time, location, src)
        except Exception as e:
            print("Something went wrong")
            await self.send_exception(message, e)
        self.lock.release()