require('dotenv').config();
import Nightmare from 'nightmare';
import { Client } from 'discord.js';
const nightmare = new Nightmare({ show: false })
const bot = new Client();

const TOKEN = process.env.TOKEN;

const ignore = ["This listing is far from your current location.", "See listings near me"]

const location_regex = /Listed (.*) in (.*)/
const url_regex = /https:\/\/www.facebook\.com\/marketplace\/item\/.*/

bot.login(TOKEN);

bot.on('ready', () => {
    console.info(`Logged in as ${bot.user.tag}!`);
});

bot.on('message', msg => {
    if (url_regex.test(msg.content)) {
      nightmare.goto(msg.content)
      .evaluate(() => {
        return document.getElementsByTagName("span")
      })
      .then((elements: HTMLCollection) => {
        let name = "N/A"
        let price = "N/A"
        let time = "N/A"
        let location = "N/A"
        let count = 1;
        for (const el of elements) {
          if (el.textContent != "" && !ignore.includes(el.textContent)) {
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
        msg.channel.send(`
        Name: ${name}
        Price: ${price}
        Listed: ${time}
        Location: ${location}
        `)
      })
    }
  });