import os
import pymongo
from pymongo import MongoClient
from flask import Flask, redirect, url_for,render_template,request
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from forms import SignUpForm, Dropdown
from connection import ApiConnection
from dispydactyl import PterodactylClient
#from flask_caching import Cache

app = Flask(__name__)

#cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.secret_key = b"random bytes representing flask secret key"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"      # !! Only in development environment.
app.config["DISCORD_CLIENT_ID"] = 789981648925098056
app.config["DISCORD_CLIENT_SECRET"] = "---"
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"
app.config["DISCORD_BOT_TOKEN"] = "---"

discord = DiscordOAuth2Session(app)
api = ApiConnection()

cluster = MongoClient('----')
collection = cluster['DisCloud']['info']

@app.route("/")
def index():
    if not discord.authorized:
        return render_template("index.html", t=False)

    return render_template("index.html", t=True)


@app.route("/login/")
def login():
    return discord.create_session(scope=["email","identify","guilds.join"])

@app.route("/dashboard/")
@requires_authorization
def dashboard():
    data = collection.find_one({"_id":discord.fetch_user().id})
    if not data:
        return redirect('/signup/')

    used = api.get_resource(discord.fetch_user())
    return render_template("dashboard.html",user=discord.fetch_user(), data=data,used=used)

@app.route("/callback/")
def callback():
    data = discord.callback()
    user=discord.fetch_user()
    user.add_to_guild(793869104142090240)
    if not collection.find_one({"_id":user.id}):
         return redirect('/signup/')
    else:
        redirect_to = data.get("redirect", "/dashboard")
        return redirect(redirect_to)

@app.route("/signup/",methods=['GET','POST'])
@requires_authorization
def signup():
    discord_user = discord.fetch_user()
    form = SignUpForm()
    if request.method == "POST":
        form_result = request.form.to_dict()
        api.set_password(discord_user, form_result['password'])
        return redirect('/dashboard/')

    return render_template('signup.html',form=form)

@app.route("/dashboard/servers/create",methods=['GET','POST'])
@requires_authorization
def create_server():
    form = Dropdown()
    user = discord.fetch_user()
    used_data=api.get_resource(user)
    if form.is_submitted():
        result = request.form.to_dict()
        t =api.create_server_user(discord.fetch_user(),result)
        return redirect('/dashboard/servers/')

    data = collection.find_one({"_id":discord.fetch_user().id})
    return render_template('create.html',user=discord.fetch_user(),used=api.get_resource(user),data=data,form=form)


@app.route("/dashboard/servers/")
def servers():
    user = discord.fetch_user()

    server = api.get_server(user)
    return render_template('servers.html',user=user,server=server)


@app.route("/tos/")
def tos():
    return render_template('tos.html')

@app.route("/privacypolicy/")
def privacy():
    return render_template('privacy.html')

@app.route("/plans/")
def plans():
    if not discord.authorized:
        return render_template("test.html", t=False)

    return render_template("test.html", t=True)

@app.route("/dashboard/profile/",methods=['GET','POST'])
def profile():
    user = discord.fetch_user()
    if request.method == "POST":
        password = request.form.to_dict()
        api.reset_password(user, password['password'])
        print('f')
        redirect(request.url)

    panel_info=api.get_user(user)
    return render_template('profile.html', user=user,info=panel_info, data=collection.find_one({"_id":user.id}))


@app.route("/logout/")
def logout():
    discord.revoke()
    return redirect(url_for(".index"))

@app.route("/dashboard/modify/id=<name>", methods=['GET','POST'])
def modify_server(name):
    user = discord.fetch_user()
    server = api.get_server(user)
    if request.method == "POST":
        form_result = request.form.to_dict()
        client = PterodactylClient('https://panel.disanime.ml/', '---')
        client.servers.update_server_build(server_id=server[int(name)]['data']['attributes']['id'],allocation_id=server[int(name)]['data']['attributes']['allocation'],memory_limit=form_result['ram'], swap_limit=0, disk_limit=form_result['disk'], cpu_limit=form_result['cpu'], io_limit=500,
        database_limit=0, allocation_limit=0, oom_disabled=True)
        return redirect('/dashboard/servers/')

    data = collection.find_one({"_id":discord.fetch_user().id})
    return render_template('modify.html',user=user,used=api.get_resource(discord.fetch_user()),data=data,server=server[int(name)])

@app.route("/delete/<name>")
def delete_server(name):
    client = PterodactylClient('https://panel.disanime.ml/', '---')
    client.servers.delete_server(name)
    return redirect('/dashboard/servers/')

@app.errorhandler(404)
def error(e):
    return render_template('error.html', er=404)

@app.errorhandler(Unauthorized)
def error(e):
    return render_template('error.html', er=401)


if __name__ == "__main__":
    app.run(debug=True)
