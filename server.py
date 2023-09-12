from flask import Flask, request, send_from_directory, render_template, jsonify
from notifications import notify
from flask_sqlalchemy import SQLAlchemy
from secrets import secret
import os
import urllib.parse

# authorization key for this server's API
API_KEY = secret("API_KEY")

app = Flask(__name__)

# settings for SQL database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# database model for Player
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    playtime = db.Column(db.Integer, unique=False, nullable=False)

if __name__ == '__main__':
    # was used to recreate the database
    with app.app_context():
        db.create_all()

# temporary dict for checking linking requests
linking_requests = {}

def is_authorized(headers: dict) -> bool:
    """Checks if the received headers contain a valid API KEY."""

    received_api_key = headers.get("api-key")
    if received_api_key != API_KEY:
        return False
    else:
        return True

@app.route("/")
def home_page():
    """Webserver's homepage."""
    return render_template("index.html")


@app.route('/favicon.ico')
def favicon():
    """Loads server's favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'static/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.route('/request', methods=['POST', 'GET'])
def request_playtime():
    """Either sets or returns the playtime of a set player."""

    # API-KEY check
    if not is_authorized(request.headers):
        return jsonify(message="Invalid API-KEY"), 403

    # fetching the username parameter
    username = request.args.get("username")
    if username is not None:
        # ignoring differences between upper-case and lower-case letters in names
        username = username.lower()
    else:
        return jsonify(messsage="Missing the username argument."), 400

    # fetching the player's data from the database
    player = Player.query.filter_by(username=username).first()

    if request.method == 'POST':
        # setting player's playtime

        # fetching the playtime parameter
        playtime = request.args.get("playtime")
        if playtime is None:
            return jsonify(messsage="Missing the playtime argument."), 400

        # checking the correct format of playtime, so it is not a string for example
        try:
            playtime = int(playtime)
        except ValueError:
            return jsonify(message="Incorrect playtime format."), 400

        if player is None:
            # the player has not yet been added to the database -> adding him to the database
            player = Player(username=username, playtime=playtime)
            db.session.add(player)
        else:
            # player is already in the database
            # checking if the sent-in playtime is actually more than the currently saved playtime
            # or if the change is enforced
            force_change = request.args.get("force_change")
            if player.playtime <= playtime or force_change:
                player.playtime = playtime
            else:
                print(f"Playtime set for {username} was {playtime} which is lower than saved {player.playtime}.")

        # committing any changes made to the database
        db.session.commit()

        return jsonify(message="Successfully updated the player's data."), 200
    else:
        # retrieving player's playtime

        # fetching the player's data
        # will return 0 playtime if no player is found
        playtime = player.playtime if player is not None else 0

        # returning a response containing the player's playtime
        return jsonify(playtime), 200


@app.route('/notify', methods=['POST'])
def notify_me():
    """Sends a notification using notify-run."""

    # API-KEY check
    if not is_authorized(request.headers):
        return jsonify(message="Invalid API-KEY"), 403

    if request.method == "POST":
        # retrieves the message argument
        message = request.args.get("message")

        # decoding
        message = urllib.parse.unquote(message)

        # sending the notification
        notify(message)
        print(f"Sent message: {message}")
        return jsonify(message="Message sent."), 200

@app.route("/top_times", methods=["GET"])
def top_times():
    """Returns the X amount of players with the highest playtime."""

    # API-KEY check
    if not is_authorized(request.headers):
        return jsonify(message="Invalid API-KEY"), 403

    if request.method == "GET":
        # getting the desired amount of top players
        amount = request.args.get("amount")

        # checking the correct format, if it isn't a string for example
        try:
            amount = int(amount)
        except ValueError:
            return jsonify(message="Incorrect amount format."), 400

        # preventing accessing unnecessary large quantities of data
        if amount > 100:
            return jsonify(message="Amount was too high."), 400

        # retrieving the top players data model
        top_players = Player.query.order_by(
            Player.playtime.desc()).limit(amount).all()

        # formatting their usernames and playtimes in a dictionary
        top_times_dict = {
            player.username: player.playtime
            for player in top_players
        }

        # returning a response containing the data
        return jsonify(top_times_dict), 200


@app.route("/link", methods=["GET", "POST"])
def link():
    """Can receive or return current requests for username linking."""

    # API-KEY check
    if not is_authorized(request.headers):
        return jsonify(message="Invalid API-KEY"), 403

    # fetching the roblox username parameter
    roblox_username = request.args.get("roblox_username")
    if roblox_username is None:
        return jsonify(messsage="Missing the username argument."), 400

    if request.method == "POST":
        # setting a new or changing a current linking request

        # fetching the status parameter, used to determine what to do with a said request
        status = request.args.get("status")
        if status is None:
            return jsonify(message="Missing the status argument."), 400
        else:
            status = int(status)

        # performing actions based on the status
        if status == 2:
            # request should be removed

            # removing the username from the linking requests
            if roblox_username in linking_requests:
                del linking_requests[roblox_username]
                return jsonify(message="Removed the linking request."), 200
            else:
                # linking request was not found
                return jsonify(
                    message="This username has no longer an active request."
                ), 400

        elif status == 0:
            # a new request was issued

            # fetching the discord name parameter
            discord_name = request.args.get("discord_name")
            if discord_name is None:
                return jsonify(message="Missing the discord_name argument."), 400

            # saving the new linking request
            linking_requests[roblox_username] = {
                "discord_name": discord_name,
                "status": status
            }
            return jsonify(
                message="Successfully created a new linking request."), 200
        else:
            # other statuses don't require any action from this server, so the change is simply recorded
            if roblox_username in linking_requests:
                linking_requests[roblox_username]["status"] = status
                return jsonify(message="Successfully updated the status."), 200
            else:
                # linking request was not found for the roblox username
                return jsonify(
                    message="This username has no active request."), 400

    elif request.method == "GET":
        # retrieving the discord name and status for the requested roblox username

        if roblox_username not in linking_requests:
            # linking request was not found for the roblox username
            return jsonify(message="This username has not initiated a linking request."), 400
        else:
            return jsonify((roblox_username, linking_requests[roblox_username])), 200


@app.route("/all_linking_requests", methods=["GET"])
def all_link_requests():
    """Returns all linking requests that are active on this server."""

    # API-KEY check
    if not is_authorized(request.headers):
        return jsonify(message="Invalid API-KEY"), 403

    if request.method == "GET":
        # simply returning the server's dictionary of linking requests
        return jsonify(linking_requests), 200
