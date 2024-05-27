import os

from generator.PageManager import PageManager
from generator.ReactGenerator import ReactGenerator


path = PageManager.get_page_path("2086036019", "test1")
PageManager.go_to_main_dir()
print(os.getcwd())
ReactGenerator.agregarSectionInformativa("nosotros",path, "kjahsdkhaskdhkljashdlasdhkasjhdlkjahskld")