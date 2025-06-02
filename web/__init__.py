from flask import Flask, render_template, request
from time import sleep

app = Flask(__name__)
PASSWORD = "01NOT4NEA5YGUESS"

@app.route('/', methods=['GET', 'POST'])
def index():
    guess = request.args.get('password')
    
    for password_char, guess_char in zip(PASSWORD, guess):
        if password_char != guess_char:
            return "Password is incorrect"
        sleep(0.1)
    return "Password is correct"

if __name__ == '__main__':
    app.run(debug=True)