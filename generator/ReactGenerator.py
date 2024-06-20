import json
import os
import threading
import requests
import json
import cloudconvert
import markdown

from resources import utils, CONSTANTS

class ReactGenerator:

    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ReactGenerator()
        return cls._instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReactGenerator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Comprobar si ya está inicializado
            self._initialized = True  # Marcar como inicializado
            cloudconvert.configure(api_key=CONSTANTS.FILE_CONVERTION_API_KEY, sandbox=False)

    @staticmethod
    def _convert_file(source, destination):
        # Crear trabajo
        job = cloudconvert.Job.create(payload={
            "tasks": {
                'upload':
                {
                    'operation': 'import/upload'
                },
                'convert':
                {
                    'operation': 'convert',
                    'input': 'upload',
                    'output_format': 'ico'
                },
                'export':
                {
                    'operation': 'export/url',
                    'input': 'convert'
                }
            },
            "redirect": True
        })

        #Subir archivo
        upload_task_id = job['tasks'][0]['id']
        upload_task = cloudconvert.Task.find(id=upload_task_id)
        cloudconvert.Task.upload(file_name=source, task=upload_task)

        #Esperar a que finalice el trabajo
        cloudconvert.Job.wait(id=job['id'])

        #Obtener resultado
        job = cloudconvert.Job.find(id=job['id'])
        for task in job['tasks']:
            if task['name'] == 'export':
                url = task['result']['files'][0]['url']
        response = requests.get(url)

        #Guardarlo
        with open(destination, 'wb') as f:
            f.write(response.content)

    @staticmethod
    def set_favicon(page_path):
        utils.go_to_dir_from_main(page_path)
        favicon_path = os.getcwd() + "\\components\\Logo.png"
        utils.go_to_dir("src")
        utils.go_to_dir("app")
        favicon = ReactGenerator._convert_file(favicon_path, os.getcwd() + "\\favicon.ico")
        utils.go_to_main_dir()

    @staticmethod
    def set_colors(page_path, color:str):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        filename = os.getcwd() + "\\custom_tailwind_colors.ts"
        with open(filename, "r") as file:
            colors_file = file.readlines()

        color = color[1:len(color)]
        url = CONSTANTS.TAILWIND_COLOR_API_URL + "/customColor/" + color
        response = requests.get(url=url)
        colors_dict = json.loads(response.text)
        output = {}
        text = "export const CUSTOM_COLORS = {\n"
        for key in colors_dict["customColor"].keys():
            text += key + ": \"" + colors_dict["customColor"][key] + "\",\n"
        text = text[:len(text) - 2] + "};"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()

    @staticmethod
    def set_collection(page_path, collection):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        text = f"""export const Nombre_Esquema = "{collection}";"""
        filename = os.getcwd()+ "\\collection.ts"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()

    @staticmethod
    def set_address(page_path, address):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        text = f"""export const LINK = "{address}";"""
        filename = os.getcwd() + "\\link.ts"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()

    @staticmethod
    def set_tab_name(page_path, tab_name):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        text = f"""export const TAB_NAME = "{tab_name}";"""
        filename = os.getcwd() + "\\tab_name.ts"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()


    @staticmethod
    def generarHeader(page_path, title = None, color = None, logo = False):
        if logo:
            ReactGenerator.set_favicon(page_path)

    @staticmethod
    def set_footer_email(page_path, email):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        print(email)
        with open("footer_contact_info.ts", 'r') as file:
            lines = file.readlines()

        # Encontrar el índice de la definición del array SECTIONS
        start_index = next(i for i, line in enumerate(lines) if 'export const FOOTER_CONTACT_INFO' in line)

        # Buscar la línea a modificar
        for line in lines:
            if "Email" in line:
                line = f'    {{ label: "Email", value: "{email}" }},\n'

        # Escribir los cambios de vuelta al archivo
        with open("footer_contact_info.ts", 'w') as file:
            file.writelines(lines)
        utils.go_to_main_dir()

    @staticmethod
    def set_footer_location(page_path, location):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        print(email)
        with open("footer_contact_info.ts", 'r') as file:
            lines = file.readlines()

        # Encontrar el índice de la definición del array SECTIONS
        start_index = next(i for i, line in enumerate(lines) if 'export const FOOTER_CONTACT_INFO' in line)

        # Buscar la línea a modificar
        for line in lines:
            if "Ubicacion" in line:
                line = f'    {{ label: "Ubicacion", value: "{location}" }},\n'

        # Escribir los cambios de vuelta al archivo
        with open("footer_contact_info.ts", 'w') as file:
            file.writelines(lines)
        utils.go_to_main_dir()


    @staticmethod
    def generarFooter(page_path, email = None, location = None):
        if email is not None:
            ReactGenerator.set_footer_email(page_path, email)
        if location is not None:
            ReactGenerator.set_footer_location(page_path, email)

    @staticmethod
    def add_section(page_path, section_name):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        print(section_name)
        with open("sections.ts", 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Encontrar el índice de la definición del array SECTIONS
        start_index = next(i for i, line in enumerate(lines) if 'export const SECTIONS' in line)
        file_name = section_name.replace(" ", "_").replace("?", "").replace("!", "").replace("¡", "").replace("¿", "")

        # Nueva entrada en formato JSON
        new_entry = f'  {{ name: "{section_name}", component: "{file_name}" }},\n'
        print(new_entry)

        # Insertar la nueva entrada en la lista SECTIONS
        if "E-Commerce" in section_name:
            lines.insert(start_index  + 1, new_entry)
        else:
            lines.insert(len(lines) - 1, new_entry)

        # Escribir los cambios de vuelta al archivo
        with open("sections.ts", 'w', encoding='utf-8') as file:
            file.writelines(lines)
        utils.go_to_main_dir()

    @staticmethod
    def remove_section(page_path, section_name, total_remove=True):
        utils.go_to_dir_from_main(page_path)
        if total_remove:
            utils.go_to_dir("constants")
            with open("sections.ts", 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Encontrar el índice de la definición del array SECTIONS
            start_index = next(i for i, line in enumerate(lines) if 'export const SECTIONS' in line)
            file_name = section_name.replace(" ", "_").replace("?", "").replace("!", "").replace("¡", "").replace("¿", "")

            # Buscar la línea a eliminar
            entry_to_remove = f'  {{ name: "{section_name}", component: "{file_name}" }},\n'
            try:
                lines.remove(entry_to_remove)
                print(f'Sección "{section_name}" eliminada.')
            except ValueError:
                pass

            # Escribir los cambios de vuelta al archivo
            with open("sections.ts", 'w', encoding='utf-8') as file:
                file.writelines(lines)
            utils.go_to_dir_from_main(page_path)
        file_path = os.getcwd() + "\\components\\" + file_name + ".tsx"
        try:
            os.remove(file_path)
            print(f"Archivo {file_path} eliminado con éxito.")
        except FileNotFoundError:
            print(f"El archivo {file_path} no existe.")
        except PermissionError:
            print(f"No tienes permiso para eliminar el archivo {file_path}.")
        except Exception as e:
            print(f"Ha ocurrido un error al intentar eliminar el archivo {file_path}: {e}")

    @staticmethod
    def _convert_html_to_jsx(html):
        tag_to_jsx = {
            'h1': 'text-3xl font-bold text-customColor-800 mb-4',
            'h2': 'text-2xl font-bold text-customColor-700 mb-3',
            'h3': 'text-xl font-bold text-customColor-600 mb-2',
            'h4': 'font-bold text-customColor-500',
            'p': 'text-lg text-gray-700 mb-6',
            'ul': 'list-disc list-inside mb-6',
            'ol': 'list-decimal list-inside mb-6',
            'li': 'text-gray-700 text-left mb-2',
            'a': 'text-customColor-500 hover:underline',
            'strong': 'font-semibold',
            'em': 'italic',
            'blockquote': 'border-l-4 border-gray-400 pl-4 italic text-gray-600 mb-6',
            'code': 'bg-gray-100 rounded p-1 text-sm font-mono',
            'pre': 'bg-gray-100 rounded p-4 overflow-x-auto mb-6'
        }
        jsx = html.replace("&", "&amp;")
        jsx = jsx.replace('"', '&quot;')
        jsx = jsx.replace("'", "&apos;")
        for tag, tailwind_classes in tag_to_jsx.items():
            opening_tag = f'<{tag}>'
            closing_tag = f'</{tag}>'
            jsx_opening_tag = f'<{tag} className="{tailwind_classes}">'
            jsx_closing_tag = f'</{tag}>'
            jsx = jsx.replace(opening_tag, jsx_opening_tag)
            jsx = jsx.replace(closing_tag, jsx_closing_tag)
        return jsx

    @staticmethod
    def agregarSectionInformativa(page_path, nombre, contenido, is_update=False):
        html = markdown.markdown(contenido)
        file_name = nombre.replace(" ", "_").replace("?", "").replace("!", "").replace("¡", "").replace("¿", "")
        jsx_content = ReactGenerator._convert_html_to_jsx(html)
        tsx_template = f"""
            import React from "react";
    
            const {file_name} = () => {{
            return (
                <section
                    className="min-h-screen bg-gradient-to-b from-customColor-100 to-customColor-200 flex flex-col items-center p-8 w-full">
                    <div className="min-h-screen flex flex-col w-full bg-white rounded-lg shadow-lg p-6 text-left">
                        {jsx_content}
                    </div>
                </section>
            );
            }};
    
            export default {file_name};
        """
        utils.go_to_dir_from_main(page_path)
        with open(os.getcwd() + "\\components\\" + file_name + ".tsx", "w", encoding="utf-8") as file:
            file.write(tsx_template)
        if not is_update:
            ReactGenerator.add_section(page_path, nombre)
        utils.go_to_main_dir()