from server import app

if __name__ == "__main__":
    print("Server is online.")
    app.run(host='0.0.0.0', port=9100)
