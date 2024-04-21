from flask import Flask, request
import generator

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hola, mundo!'

@app.route('/create-next-app')
def create_next_app():
    #Se crea el directorio para el usuario, luego se crea el directorio para la página y en él se crea el proyecto
    generator.go_to_main_dir()
    generator.go_to_dir(request.json.get("user"))
    generator.go_to_dir(request.json.get("page_name"))
    generator.create_project(request.json.get("page_name"))

    return 'www.' + request.json.get("page_name") + ".com", 200

if (__name__ == '__main__'):
    app.run(host='0.0.0.0', port=5000)
