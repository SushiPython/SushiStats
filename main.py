from quart import Quart, render_template, request, redirect, send_from_directory
import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import random
import datetime
import re
import motor.motor_asyncio
import requests
import aiohttp
import requests
import ast
import json

app = Quart(__name__, static_folder="static")


@app.route('/robots.txt')
async def static_from_root():
    return await send_from_directory(app.static_folder, request.path[1:])

jinja_env = Environment(
    loader=FileSystemLoader(searchpath='templates'),
    autoescape=select_autoescape(['html', 'xml']),
    enable_async=True,
    trim_blocks=True,
    lstrip_blocks=True)

friend_counts = {}

color_codes = {
    '0': '#000000',
    '1': '#0000be',
    '2': '#00be00',
    '3': '#00bebe',
    '4': '#be0000',
    '5': '#be00be',
    '6': '#ffaa00',
    '7': '#bebebe',
    '8': '#3f3f3f',
    '9': '#3f3ffe',
    'a': '#3ffe3f',
    'b': '#3ffefe',
    'c': '#fe3f3f',
    'd': '#fe3ffe',
    'e': '#fefe3f',
    'f': '#ffffff'
}

key = os.getenv('key')
mongo = os.getenv('mongo')

client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb+srv://dbUser:{mongo}@cluster0.at4iw.mongodb.net/<dbname>?retryWrites=true&w=majority")

c = client.test.users

other_style_codes = {
    'l': 'font-weight: bold;'
}

def convert_color_codes_to_html(code, symbol, include_raw=False):
    current_color = None
    current_effects = set()
    if not isinstance(code, str):
        code = code.decode()
    output = ''
    text_output = ''
    i = -1
    while i < len(code) - 1:
        i += 1
        if code[i] == '&':
            i += 1
            if code[i] in color_codes:
                if current_color:
                    output += '</span>'
                color = color_codes[code[i]]
                style = f'color:{color}'
            elif code[i] in other_style_codes:
                current_effects.add(code[i])
                style = other_style_codes[code[i]]
            output += f'<span style="{style}">'
            current_color = color
        else:
            output += code[i]
            text_output += code[i]
    if current_color:
        output += '</span>'
    if include_raw:
        return output, text_output
    return output

async def fetch_json(url):
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
      return await response.json()


app.jinja_env.globals[
    'convert_color_codes_to_html'] = convert_color_codes_to_html
app.jinja_env.globals['round'] = round
app.jinja_env.globals['datetime'] = datetime
app.jinja_env.globals['int'] = int
def su(n):
  print(n)
  return re.sub('&.', '', n)
app.jinja_env.filters['su'] = su
app.jinja_env.filters['nu'] = lambda n: '{:,}'.format(n) if n else "0"
app.jinja_env.filters['fr'] = lambda n: datetime.datetime.fromtimestamp((n-(n%1000))/1000).strftime("%x %X")

@app.route('/')
async def main():
    return await render_template('index.html')


@app.route('/proxy', methods=["GET", "POST"])
async def proxy():
    if request.method == "POST":
        data = await request.form
        return redirect(f'/stats/{data["ign"]}')
    if request.method == "GET":
      return redirect('/')

async def getUnix(item, data):
  if item not in data:
    return 'Private'
  if data[item] is None:
    return 'Private'
  else:
    return datetime.date.fromtimestamp(int(str(data[item])[:-3]))


@app.route('/hypixel/player/stats/<uuid>')
async def redir(uuid):
  gm = await fetch_json("https://api.ashcon.app/mojang/v2/user/" + uuid)
  username = gm['username']
  return redirect(f'/stats/{username}', 302)

@app.route('/stats/<user>', methods=["GET", "POST"])
async def stats(user):
  if request.method == "GET":
    print(request.headers.get('Cf-Connecting-Ip'))
    data = await fetch_json(f'https://api.slothpixel.me/api/players/{user}?key={key}')
    friend_data = await fetch_json(f'https://api.slothpixel.me/api/players/{user}/friends?key={key}')
    guild_data = await fetch_json(f'https://api.slothpixel.me/api/guilds/{user}?key={key}')
    first_login = await getUnix('first_login', data)
    last_login = await getUnix('last_login', data)
    created = await getUnix('created', guild_data)
    friends = len(friend_data)
    if 'guild' in guild_data:
      return await render_template('noguild.html', data=data, user=user, friends=friends, first_login=first_login, last_login=last_login)
    else:
      if 'tag' in guild_data:
        tag = guild_data['tag']
      else:
        tag = 'None'
      d = []
      for members in guild_data['members']:
        if members['rank'] == 'Guild Master':
          d.append(members['uuid'])
      gm = await fetch_json("https://api.ashcon.app/mojang/v2/user/" + str(d[0]))
        
      return await render_template('stats.html', data=data, user=user, guild_data=guild_data, guild_members=len(guild_data['members']), created=created, gm=gm['username'], friends=friends, first_login=first_login, last_login=last_login, tag=tag)

@app.route('/friends/<user>')
async def friends(user):
  id = await fetch_json('https://api.mojang.com/users/profiles/minecraft/'+user)
  id = id['id']
  f_users = requests.get('https://plancke.io/hypixel/player/friends/fetch.php?begin=0&uuid='+id).json()
  d = f_users['list']
  return await render_template('friends.html', f_users=d, user=user)

@app.errorhandler(404)
async def page_not_found(e):
    return await render_template('error.html', errorCode=404, err="Page Not Found"), 404

@app.errorhandler(500)
async def server_error(e):
    return await render_template('error.html', errorCode=500, err=""), 500

app.run(host='0.0.0.0', port=8080)
