from flask import Flask, request, send_from_directory, render_template
from notifications import notify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    playtime = db.Column(db.Integer, unique=False, nullable=False)


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'static/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/request', methods=['POST', 'GET'])
def request_playtime():
    if request.method == 'POST':
        name = request.args.get("name").lower()
        playtime = request.args.get("playtime")

        try:
            playtime = int(playtime)
        except ValueError:
            return "Mission failed"

        player = Player.query.filter_by(username=name).first()
        if player is None:
            player = Player(
                username=name,
                playtime=playtime
            )
            db.session.add(player)
        else:
            if player.playtime <= playtime:

                player.playtime = playtime
        db.session.commit()

        return 200
    else:
        name = request.args.get("name").lower()
        player = Player.query.filter_by(username=name).first()
        if player is None:
            return "unknown"
        else:
            return str(player.playtime)


@app.route('/notify', methods=['POST'])
def notify_me():
    if request.method == "POST":
        message = request.args.get("message")
        notify(message)
        print(f"Sent message: {message}")
        return "Notified successfully."


@app.route("/topten")
def top_ten_player():
    top_players = Player.query.order_by(Player.playtime.desc()).limit(50).all()
    message = ""
    for player in top_players:
        message += f"{player.username}*{player.playtime};"
    return message


def run():
    print("Booting up server.")
    app.run(host='0.0.0.0', port=8095)
    print("Server booted up.")
