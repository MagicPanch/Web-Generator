from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hola, mundo!'

@app.route('/create-next-app')
def create_next_app():
    #proceso = subprocess.Popen(['powershell', '-Command', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #proceso.stdin.write('pwd')
    #proceso.stdin.flush()
    #proceso.stdin.write("npx create-next-app nombre-de-tu-proyecto --typescript --eslint --tailwind")

    return 'Next app created', 200


if (__name__ == '__main__'):
    app.run(host='0.0.0.0', port=5000)