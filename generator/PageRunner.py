import threading
from abc import abstractmethod


class PageRunner(threading.Thread):
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.
    @abstractmethod
    def __init__(self, user, page_name, page_port):
        super().__init__()
        self._user = user
        self._page_name = page_name
        self._page_port = page_port
        self._running_thread = None
        self._target = None
        self._process = None
        self._stop_event = threading.Event()
        self._restarted = threading.Event()
        self._restarted.set()
        pass

    def get_user(self) -> str:
        return self._user

    def get_name(self) -> str:
        return self._page_name

    def get_port(self) -> int:
        return self._page_port

    def set_target(self, target):
        #Se asigna el nuevo target con la funcion a ejecutar.
        #Si el hilo aun esta ejecutandose, aguarda a que el mismo finalice.
        if self._target == None:
            self._target = target
        else:
            self.join_running_thread()
            self._target = target

    def set_process(self, process):
        if self._process == None:
            self._process = process
        else:
            self.join_running_thread()
            self.set_process(process)

    def join_running_thread(self):
        #Se espera a que finalice el proceso que se esta ejecutando en el hilo
        #Luego se levanta el flag Stop y se limpia el target anterior
        if (self._process is not None):
            self._process.wait()
            self._process = None
        self.stop()
        self._target = None

    def stop(self):
        self._stop_event.set()

    def restart(self):
        self._restarted.set()  # Indicar que se ha reiniciado el hilo
        self._stop_event.clear()  # Reiniciar la señal de detención

    @abstractmethod
    def run(self):
        pass

