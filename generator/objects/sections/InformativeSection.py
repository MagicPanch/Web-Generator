from generator.objects.sections.Section import Section


class InformativeSection(Section):

    def __init__(self, title):
        super().__init__("informativa", title)
        self._text = None

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text

