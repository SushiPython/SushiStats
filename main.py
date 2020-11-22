from flask import Flask, render_template, request, redirect
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import random
import datetime
import re
import pymongo

app = Flask(__name__)

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

client = pymongo.MongoClient(f"mongodb+srv://dbUser:{mongo}@cluster0.at4iw.mongodb.net/<dbname>?retryWrites=true&w=majority")

c = client.data.users




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

def fCount(user, uuid):
  if user not in friend_counts:
    friends = requests.get(f'https://api.hypixel.net/friends?key={key}&uuid={uuid}').json()
    friend_counts[user] = len(friends['records'])
    if not c.find_one({"username":user}):
      c.insert_one({
        "username": user,
        "uuid": uuid
      })
  return friend_counts[user]

app.jinja_env.globals[
    'convert_color_codes_to_html'] = convert_color_codes_to_html
app.jinja_env.globals['round'] = round
app.jinja_env.globals['datetime'] = datetime
app.jinja_env.globals['int'] = int
def su(n):
  print(n)
  print(type(n))
  return re.sub('&.', '', n)
app.jinja_env.filters['su'] = su
app.jinja_env.filters['nu'] = lambda n: '{:,}'.format(n) if n else "0"
app.jinja_env.filters['fr'] = lambda n: datetime.datetime.fromtimestamp((n-(n%1000))/1000).strftime("%x %X")

@app.route('/')
def main():
    return render_template('index.html')


@app.route('/proxy', methods=["GET", "POST"])
def proxy():
    if request.method == "POST":
        data = request.form
        return redirect(f'/stats/{data["ign"]}', 302)
    if request.method == "GET":
      return redirect('/', 302)


@app.route('/stats/<user>', methods=["GET", "POST"])
def stats(user):
    if request.method == "GET":
        uuid = requests.get("https://api.ashcon.app/mojang/v2/user/" + user).json()
        data = requests.get(f'https://api.slothpixel.me/api/players/' + uuid['uuid'] + '?key={key}').json()
        data2 = requests.get(
            f'https://api.hypixel.net/player?name={user}&key={key}').json()
        print(data)
        return render_template('stats.html', data=data, data2=data2)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', errorCode=404, err="Page Not Found"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html', errorCode=500, err="API Ratelimit / Incorrect Username"), 500

app.run(host='0.0.0.0', port=8080)
