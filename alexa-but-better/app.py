from flask import Flask, request
from agent import *

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET123"

@app.route('/restaurant')
def book_restaurant():
    prompt = request.args.get('prompt')
    use_multion(prompt)

if __name__ == '__main__':
    app.run(debug=True, port=5000)