from generator.objects.sections.Section import Section


class InformativeSection(Section):

    def __init__(self, title):
        super().__init__("informativa", title)
        self._title = title
        self._texts = {}

    def get_texts(self):
        return self._texts

    def set_texts(self, texts):
        self._texts = texts

