# RASA to Telegram
Tutorial para hacer la conexión de un chatbot desarrollado en RASA con Telegram

## Instalación
### Rasa 3.1.0
#### Instrucciones

- Con el venv activado, ejecutar el comando
``` pip install rasa==3.1 ```
- Ir a venv/Lib/site-packages/rasa/core/channels/channel.py y encontrar el método get_metadata(self, request: Request)
- Remplazar la definición del método por
    ```python
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
        text = 'img.jpg'  # set the text to the file name
      elif msg.document is not None:
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
