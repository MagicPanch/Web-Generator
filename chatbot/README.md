# WebGenerator
Guía de instalación y ejecución del proyecto desarrollado por el grupo Design Label para la cursada 2024 de la materia Ingeniería de Software

## Instalación

### Python
#### Instrucciones

- Es necesario instalar la versión 3.8 de Python
- Verificar que la variable de entorno del sistema "PATH" tenga una entrada apuntando al directorio donde esté instalado Python. De no estar, agregarla y reiniciar la PC para guardar los cambios.
- Con python instalado, posicionarse en el directorio del proyecto, abrir una terminal y ejecutar el comando
``` python -m venv venv ``` para crear un entorno virtual el el que ejecutar el proyecto.
- Dentro de esa terminal, ejecutar los comandos ``` cd venv/Scripts ``` ``` ./Activate ``` para activar el venv y regresar al directorio original del proyecto.
- Ejecutar el comando ``` python -m pip install --upgrade pip ``` para actualizar pip y una vez que termine ejecutar ``` pip install -r requirements.txt ``` para instalar las dependencias del proyecto.
- Cuando finalice la instalación, actualizar la variable de entorno del sistema "PATH" agregando una entrada que apunte al directorio "venv/Scripts" ubicado dentro del proyecto.
- Además, en las variables de usuario del sistema crear la entrada "PythonPath" que apunte al directorio donde se encuentra el proyecto.

### Rasa 3.1.0
#### Instrucciones

- Con el venv activado, ejecutar el comando
``` pip install rasa==3.1 ```
- Ir a venv/Lib/site-packages/rasa/core/channels/channel.py y encontrar el método get_metadata(self, request: Request)
- Remplazar la definición del método por
    ```python
    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        metadata=request.json
        return metadata
    ```
- Ir a venv/Lib/site-packages/rasa/core/channels/telegram.py y encontrar el método blueprint (línea 190 aprox)
- En él, se tiene el siguiente bloque if (línea 220 aprox):
  ```python
      if self._is_button(update):
        msg = update.callback_query.message
        text = update.callback_query.data
      elif self._is_edited_message(update):
        msg = update.edited_message
        text = update.edited_message.text
      else:
        msg = update.message
        if self._is_user_message(msg):
          text = msg.text.replace("/bot", "")
        elif self._is_location(msg):
          text = '{{"lng":{0}, "lat":{1}}}'.format(
            msg.location.longitude, msg.location.latitude
          )
        else:
            return response.text("success")
  ```
- Agregar en el mismo nivel de identación:
  ```python    
        elif msg.photo is not None:  # check if message contains an image
            text = 'photo'
        elif msg.document is not None:   # check if message contains a document
            if "image" in msg.document.mime_type: # check if document is an image
                text = 'photo.document'
            else:
                text = 'archivo.csv'
  ```
- Antes de
  ```python    
    else:
        return response.text("success")
  ```

### Chocolatey
Es un gestor de paquetes para windows

#### Instrucciones

- Hay que abrir como administrador una terminal de PoweShell y ejecutar el comando ``` Get-ExecutionPolicy ```
- Si el comando anterior retorna RESTRICTED hay que ejecutar el comando ```Set-ExecutionPolicy AllSigned```
- Finalmente hay que ejecutar el comando 
```Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))```

### Ngrok 3.8.0
#### Instrucciones

- Con Chocolatey ya instalado, ejecutar el comando ```choco install ngrok```
- Después hay que registrarse en https://dashboard.ngrok.com/signup
- Con Ngrok instalado y logueado en la página les aparece un tutorial para la instalación en windows. De ese tutorial hay que copiar el comando con la forma ```ngrok config add-authtoken <SU_TOKEN>```

## Uso
### Instrucciones
- Abrir una terminal de PowerShell y ejecutar el comando ```ngrok http 5005```
- Copiar la dirección que aparezca en la línea Forwarding antes de la "->"
- Abrir Web-Generator/chatbot/credentials.yml y en la línea webhook_url de la sección telegram pegar la dirección copiada + "/webhooks/telegram/webhook"
- Abrir la siguiente dirección https://api.telegram.org/bot6804076373:AAGVfw6smnTUmLXzReSdSmVHmcYvvempgI0/setWebhook?url=<WEBHOOK_URL> remplazando la parte final por la línea completa de la url en Credentials.yml
- Abrir otra terminal y posicionarse en Web-Generator/chatbot y ejecutar ```Rasa run```
- Si no hay errores se le puede hablar al bot en https://web.telegram.org/a/#6804076373
