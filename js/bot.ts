require('dotenv').config();
import puppeteer from 'puppeteer';
import { Client } from 'discord.js';
const bot = new Client();
let browser: puppeteer.Browser;
const launchBrowser = async () => {
  if (browser) return;
  browser = await puppeteer.launch({
    headless: false,
    args: [
      '--no-sandbox',
      '--disable-gpu'
    ]
  });
};

const TOKEN = process.env.TOKEN;

const ignore = ["This listing is far from your current location.", "See listings near me"]

const location_regex = /Listed (.*) in (.*)/
const url_regex = /https:\/\/www.facebook\.com\/marketplace\/item\/.*/

bot.login(TOKEN);

bot.on('ready', async () => {
  console.info(`Logged in as ${bot.user.tag}!`);
});

bot.on('message', async msg => {
  if (url_regex.test(msg.content)) {
    msg.channel.send("Seen a FBM link...")
    try {
      await launchBrowser();
      console.log("Opening page...")
      const page = await browser.newPage();
      console.log("Going to link...")
      await page.goto(msg.content, { timeout: 15000 })
      console.log("Finding spans...")
      await page.evaluate(() => {
        return document.getElementsByTagName("span")
      })
        .then((elements) => {
          console.log("Processing elements...")
          console.log(elements)
          let name = "N/A"
          let price = "N/A"
          let time = "N/A"
          let location = "N/A"
          let count = 1;
          const elementsArray = Array.from(elements)
          for (const el of elementsArray) {
            if (el.textContent != "" && !ignore.includes(el.textContent)) {
              console.log(el.textContent)
              if (count == 1) {
                name = el.textContent;
              } else if (count == 2) {
                price = el.textContent;
              } else if (location_regex.test(el.textContent)) {
                const matches = location_regex.exec(el.textContent)
                time = matches[0]
                location = matches[1]
              }
              count += 1;
            }
          }
          msg.channel.send(
`Name: ${name}
Price: ${price}
Listed: ${time}
Location: ${location}`)
        })
      await page.close()
    } catch (error) {
      console.log(error)
      msg.channel.send("An error occurred sorry")
    }
  }
});