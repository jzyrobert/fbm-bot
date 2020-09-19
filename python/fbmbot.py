import discord
import asyncio
import atexit
import re
import time
import tempfile
import string
from selenium import webdriver

ignore = ["This listing is far from your current location.", "See listings near me","›"]
location_regex = re.compile("Listed (.*) in (.*)")
full_url_regex = re.compile("(https?:\/\/)?(www.)?(facebook\.com\/)?marketplace\/item\/\d+/?")
url_id_regex = re.compile("marketplace\/item\/\d+")

name_regex = re.compile("marketplace_listing_title:\"(.*?)\"")
price_regex = re.compile("formatted_price:{text:\"(£.*?)\"}")
second_location_regex = re.compile("location_text:{text:\"(.*?)\"}")

pending_regex = re.compile("\"?is_pending\"?:true")
sold_regex = re.compile("\"?is_sold\"?:true")

userMessages = {
    "goodfbmbot" : "Thank you",
    "badfbmbot" : "I'm sorry"
}

retries = 2
minimumElements = 20
TEST_SERVER_ID = 725034603001413703

def exit_handler(client):
    if client.driver:
        client.driver.quit()

def url_matches_fbm(url):
    return full_url_regex.search(url) != None

def get_url_from_message(url):
    return "https://www.facebook.com/" + str(url_id_regex.search(url).group(0)) + "/"

def get_matching_urls(content):
    matches = [match.group() for match in re.finditer(full_url_regex, content)]
    return list(set([get_url_from_message(match) for match in matches]))

class FBMClient(discord.Client):
    async def scrape_first_method(self, message, url):
        name = "N/A"
        price = "N/A"
        time = "N/A"
        location = "N/A"
        try:
            elementsFound, spanSuccess, redirect, newUrl = self.find_spans_retry(url)
            if redirect:
                await self.send_sold_message(message, url, newUrl)
                return True
            elif not spanSuccess:
                return False
            print("Found {} spans".format(len(elementsFound)))
            for i in range(len(elementsFound)):
                el = elementsFound[i]
                elementText = ""
                try:
                    elementText = el.text
                except Exception as e:
                    print(e)
                if location_regex.match(elementText):
                    matches = location_regex.match(elementText)
                    time = matches.group(1)
                    location = matches.group(2)
                    # go in reverse
                    j = i
                    while j >= 1:
                        j -= 1
                        el = elementsFound[j]
                        elementText = ""
                        try:
                            elementText = el.text
                        except Exception as e:
                            print(e)
                        if elementText not in ignore and (elementText.startswith("£") or elementText == "FREE"):
                            price = elementText
                            name = elementsFound[j-1].text
                    break
            #Ensure name is correct
            if nameMatch := name_regex.search(self.driver.page_source):
                nameCheck = nameMatch.group(1)
                print("Regex found name as {}, currently is {}".format(nameCheck, name))
                if nameCheck != name:
                    name = nameCheck
            if name == "N/A" and price == "N/A" and time == "N/A" and location == "N/A":
                print("Something went wrong with method 1")
                return False
            else:
                output = "Name: {}\n".format(name)
                output += "Price: {}\n".format(price)
                output += "Listed: {}\n".format(time)
                output += "Location: {}".format(location)
                print(output)
                # acquire the image
                src = self.find_image_try()
                await self.send_embed(message, url, name, price, time, location, src)
                return True
        except Exception as e:
            print("Something went wrong with method 1")
            print(e)
            return False

    async def scrape_second_method(self, message, url):
        # Assumes page has been loaded
        name = "N/A"
        price = "N/A"
        location = "N/A"
        content = self.driver.page_source
        print("Sending page content to check")
        await self.send_exception(message, content)
        print("Matching regexes instead:")
        if nameMatch := name_regex.search(content):
            name = nameMatch.group(1)
            print("Found regex match {}".format(name))
        else:
            print("Failed in finding name match")
            return False
        if priceMatch := price_regex.search(content):
            price = priceMatch.group(1)
            print("Found regex match {}".format(price))
        else:
            print("Failed in finding price match")
            return False
        if locationMatch := second_location_regex.search(content):
            location = locationMatch.group(1)
            print("Found regex match {}".format(location))
        else:
            print("Failed in finding location match")
            return False
        print("Sending reduced info:")
        output = "Name: {}\n".format(name)
        output += "Price: {}\n".format(price)
        output += "Location: {}".format(location)
        print(output)
        await self.send_embed(message, url, name, price, "", location, "")
        return True

    def find_spans_retry(self, url):
        print("Attempting to load {}".format(url))
        tries = 0
        self.driver.get(url)
        currentUrl = self.driver.current_url
        if currentUrl != url:
            print("We were redirected to {}".format(currentUrl))
            return [], False, True, currentUrl
        while tries <= retries:
            time.sleep(1)
            print("Processing URL contents")
            el = self.driver.find_elements_by_tag_name("span")
            if len(el) > minimumElements:
                return el, True, False
            else:
                print("Found only {} elements, retrying..".format(len(el)))
            tries += 1
        print("Finding spans failed..")
        return el, False, False

    def find_image_try(self):
        images = self.driver.find_elements_by_tag_name("img")
        if len(images) > 0:
            return images[0].get_attribute('src')
        return False


    async def send_exception(self, message, content):
        if message.guild and message.guild.id == TEST_SERVER_ID:
            temp = tempfile.TemporaryFile()
            temp.write(str.encode(str(content)))
            temp.seek(0)
            await message.channel.send("Something went wrong, attaching log...",file=discord.File(temp, filename="log.txt"))
            temp.close()

    async def send_sold_message(self, message, url, newUrl):
        await message.channel.send("Bot was redirected to {}, could not load item.".format(newUrl))

    async def send_embed(self, message, url, name, price, time, location, imageurl):
        embed_foot_text = ""
        embed = discord.Embed(colour=0x3577E5)
        embed.set_author(name=name, url=url)
        embed.add_field(name="Price",value=price,inline=True)
        if time != "":
            embed.add_field(name="Listed",value=time,inline=True)
        embed.add_field(name="Location",value=location,inline=True)
        if imageurl != "":
            embed.set_thumbnail(url=imageurl)
        if pending_regex.search(self.driver.page_source):
            print("Found pending status")
            embed_foot_text += "**PENDING SOLD**"
        elif sold_regex.search(self.driver.page_source):
            print("Found sold status")
            embed_foot_text += "**SOLD**"
        if price == "FREE":
            embed_foot_text += "\n**Note: FREE most likely means taking offers**"
        if embed_foot_text != "":
            embed.set_footer(text=embed_foot_text)
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
        if message.author == self.user:
            print("Seen message from self")
            return
        stripped = message.content.strip().lower().translate(str.maketrans('', '', string.punctuation)).translate(str.maketrans('', '', string.whitespace))
        if stripped in userMessages:
            await message.channel.send(userMessages[stripped] + ", {}.".format(message.author.name))
            return
        name = "N/A"
        price = "N/A"
        time = "N/A"
        location = "N/A"

        matchingUrls = get_matching_urls(message.content)
        matchingCount = len(matchingUrls)
        if matchingCount == 0:
            return
        if message.guild:
            print("Received {} unique FBM url(s) from server {}, channel {}, user {}".format(matchingCount, message.guild.id, message.channel.id, message.author.name))
        else:
            print("Received {} unique FBM url(s) in private message from {}".format(matchingCount, message.author.name))
        try:
            await message.edit(suppress=True)
        except:
            print("Attempted to remove embed when did not have manage permission.")
        await self.lock.acquire()
        for url in matchingUrls:
            success = await self.scrape_first_method(message, url)
            if not success:
                await self.scrape_second_method(message, url)

        self.lock.release()
