from generator.Objects.Section import Section


class InformativeSection(Section):

    def __init__(self, title):
        super().__init__("informativa")
        self._title = title
        self._text = None
        self._texts = {}

    def get_title(self):
        return self._title

    def get_text(self):
        return self._text
    def get_texts(self):
        return self._texts

    def set_text(self, text):
        self._text = text

    def set_texts(self, texts):
        self._texts = texts

