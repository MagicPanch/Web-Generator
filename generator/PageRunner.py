import threading
from abc import abstractmethod


class PageRunner():
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.
    @abstractmethod
    def __init__(self, user, page_name, page_port):
        super().__init__()
        self._output_ready = threading.Condition()
        self._output_buffer = []
        self._user = user
        self._page_name = page_name
        self._page_port = page_port
        self._exec_process = None

    def get_user(self) -> str:
        return self._user

    def get_name(self) -> str:
        return self._page_name

    def get_port(self) -> int:
        return self._page_port

    def set_exec_process(self, process):
        with self._output_ready:
            self._exec_process = process
            self._output_ready.notify_all()

    def get_exec_process(self):
        with self._output_ready:
            while self._exec_process is None:
                self._output_ready.wait()
            return self._exec_process

    def append_output(self, output) -> bool:
        with self._output_ready:
            self._output_buffer.append(output)
            if ("Ready" in output) or ("Error" in output):
                self._output_ready.notify_all()
                return False
            else:
                return True

    def wait_for_ready(self):
        print("(" + threading.current_thread().getName() + ") " + "----PageRunner.wait_for_ready----")
        with self._output_ready:
            print("(" + threading.current_thread().getName() + ") " + "--------Salida lista, esperando")
            while not (any("Ready" in line for line in self._output_buffer) or any("Error" in line for line in self._output_buffer)):
                self._output_ready.wait()
            print("(" + threading.current_thread().getName() + ") " + "--------Espera finalizada")

