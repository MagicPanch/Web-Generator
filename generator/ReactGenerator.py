import json
import os
import threading
import requests
import json
import cloudconvert

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
    def _set_header_title(page_path, title):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        text = f"""export const HEADER_TITLE = "{title}";"""
        filename = os.getcwd() + "\\header_title.ts"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()

    @staticmethod
    def _set_header_title_color(page_path, color):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        text = f"""export const HEADER_TITLE_COLOR = "{color}";"""
        filename = os.getcwd() + "\\header_title_color.ts"
        utils.write_file(filename=filename, content=text)
        utils.go_to_main_dir()

    @staticmethod
    def generarHeader(page_path, title = None, color = None, logo = False):
        print("genero header")
        if title is not None:
            ReactGenerator._set_header_title(page_path, title)
        if color is not None:
            ReactGenerator._set_header_title_color(page_path, color)
        if logo:
            ReactGenerator.set_favicon(page_path)

    @staticmethod
    def generarFooter(dataFooter):
        print("genero footer")
        text = f""" export const FOOTER_LINKS = [
        {{
            title: "Navegacion",
            links: [
            {{ label: "Services", href: "/#services" }},
            {{ label: "Portfolio", href: "/#portfolio" }},
            {{ label: "Contact", href: "/contact-us" }},
            {{ label: "About us", href: "/about-us" }},
            ],
        }},
        ];
    
        export const FOOTER_CONTACT_INFO = {{
        title: "Contactanos",
        links: [
            {{ label: "Email", value: "{dataFooter["email"]}" }},
            {{ label: "Ubicacion", value: "{dataFooter["ubicacion"]}" }},
        ],
        }};
    
        export const SOCIALS = {{
        title: "Social",
        data: [
            {{
            image: "/facebook.svg",
            href: "https://www.facebook.com"
            }},
            {{ image: "/instagram.svg", href: "https://www.instagram.com" }},
            {{ image: "/x.svg", href: "https://twitter.com" }},
        ],
        }};
        """

        utils.go_to_dir_from_main(dataFooter["address"])
        with open(os.getcwd() + "\\components\\Footer.tsx", "w") as file:
            file.write(text)
            file.close()
        utils.go_to_main_dir()

    @staticmethod
    def add_section(page_path, section_name):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        with open("sections.ts", 'r') as file:
            lines = file.readlines()

        # Encontrar el índice de la definición del array SECTIONS
        start_index = next(i for i, line in enumerate(lines) if 'export const SECTIONS' in line)

        # Nueva entrada en formato JSON
        new_entry = f'  {{ name: "{section_name}", component: "{section_name}" }},\n'

        # Insertar la nueva entrada en la lista SECTIONS
        lines.insert(start_index + 1, new_entry)

        # Escribir los cambios de vuelta al archivo
        with open("sections.ts", 'w') as file:
            file.writelines(lines)
        utils.go_to_main_dir()

    @staticmethod
    def remove_section(page_path, section_name):
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("constants")
        with open("sections.ts", 'r') as file:
            lines = file.readlines()

        # Encontrar el índice de la definición del array SECTIONS
        start_index = next(i for i, line in enumerate(lines) if 'export const SECTIONS' in line)

        # Buscar la línea a eliminar
        entry_to_remove = f'  {{ name: "{section_name}", component: "{section_name}" }},\n'
        try:
            lines.remove(entry_to_remove)
            print(f'Sección "{section_name}" eliminada.')
        except ValueError:
            pass

        # Escribir los cambios de vuelta al archivo
        with open("sections.ts", 'w') as file:
            file.writelines(lines)
        utils.go_to_main_dir()


    @staticmethod
    def modificarSectionInformativa(nombre, page_path, texto):
        # genero component nuevo
        textSectionNew = f"""import React from "react";
                const {nombre} = () => {{        
                return (
                <section className="h-screen bg-blue-300 flex flex-col  items-center">
                <div className="max-w-screen  p-4  px-40">
                    <h1 className="font-bold text-2xl mb-4">
                        {nombre}
                    </h1>
                    <p>
                        {texto}
                    </p>
                </div>
                </section>
                );
                }};

                export default {nombre};
                """

        utils.go_to_dir_from_main(page_path)
        with open(os.getcwd() + "\\components\\" + nombre + ".tsx", "w", encoding="utf-8") as file:
            file.write(textSectionNew)
        utils.go_to_main_dir()

    @staticmethod
    def agregarSectionInformativa(page_path, nombre, texto):
        #genero component nuevo
        textSectionNew = f"""import React from "react";
        const {nombre} = () => {{        
        return (
        <section className="h-screen bg-blue-300 flex flex-col  items-center">
        <div className="max-w-screen  p-4  px-40">
            <h1 className="font-bold text-2xl mb-4">
                {nombre}
            </h1>
            <p>
                {texto}
            </p>
        </div>
        </section>
        );
        }};

        export default {nombre};
        """

        utils.go_to_dir_from_main(page_path)
        with open(os.getcwd() + "\\components\\"+nombre+".tsx", "w", encoding="utf-8") as file:
            file.write(textSectionNew)
        ReactGenerator.add_section(page_path, nombre)
        utils.go_to_main_dir()