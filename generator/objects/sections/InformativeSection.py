from generator.objects.sections.Section import Section


class InformativeSection(Section):

    def __init__(self, title):
        super().__init__("informativa", title)
        self._title = title
        self._texts = None

    def get_text(self):
        return self._texts

    def set_text(self, text):
        self._texts = text

