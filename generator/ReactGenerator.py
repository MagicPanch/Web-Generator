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
        utils.go_to_main_dir()
        favicon_path = os.getcwd() + "\\" + page_path + "\\components\\Logo.png"
        utils.go_to_dir_from_main(page_path)
        utils.go_to_dir("src")
        utils.go_to_dir("app")
        favicon = ReactGenerator._convert_file(favicon_path, os.getcwd() + "\\favicon.ico")

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
    def generarHeader(data):
        print("genero header")
        ReactGenerator.set_favicon(data["address"])

        text = f""""use client";
        
        import React from "react";
        import logo from '{data["addressLogo"]}';
        import Image from "next/image";
        import Link from "next/link";
        
        const Header = () =>  {{
            return(
            
                <div className=" bg-blue-500 flex  items-center justify-between h-20 px-4">
                    <div className="border-green-300 border-2  rounded h-30 w-30  bg-green-400 items-center">
                        <Image src= {{logo}}  
                        width={{100}}
                        height={{100}}
                        alt="Logo"/>
                    </div>
                    <h1 className="text-5xl text-colorTituloHeader  mb-5  font-semibold text-center flex-1">
                        {data["titulo"]}
                    </h1>
                </div>
            )
        }}
        export default Header;
        """
        configColor = f"""/** @type {{import('tailwindcss').Config}} */
        module.exports = {{
        content: [
            "./pages/**/*.{{js,ts,jsx,tsx,mdx}}",
            "./components/**/*.{{js,ts,jsx,tsx,mdx}}",
            "./app/**/*.{{js,ts,jsx,tsx,mdx}}",
        ],
        theme: {{
        extend: {{
            fontFamily: {{
                body: ["Korolev Medium"],
            }},
        colors: {{
            primary: {{
                400: "#CBEAF2",
                500: "#66b7cb",
                600: "#55a4b7",
            }},
                bgGray: "#E2E2E2",
                bgBlack: "#1C1C1C",
                colorTituloHeader : "{data["colorTitulo"]}",
            }},
            backgroundSize: {{
                "16": "4rem",
            }},
            screens: {{
                xs: "400px",
                "3xl": "1680px",
                "4xl": "2200px",
            }},
            maxWidth: {{
                "10xl": "1512px",
            }},
            borderRadius: {{
                "5xl": "40px",
            }},
            }},
            }},
            plugins: [],
        }};"""
        utils.go_to_main_dir()
        with open(os.getcwd() + "\\" + data["address"]+"\\components\\Header.tsx", "w") as file:
            file.write(text)
            file.close()

        with open(data["address"]+"\\tailwind.config.ts", "w") as file:
            file.write(configColor)
            file.close()

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

        utils.go_to_main_dir()
        with open(os.getcwd() + "\\" + dataFooter["address"] + "\\components\\Footer.tsx", "w") as file:
            file.write(text)
            file.close()

    @staticmethod
    def generarBody(dataBody):
        print("genero body")
        text = f""" export const CARDS_DATA = [
        {{
            image: "https://via.placeholder.com/300",
            title: "Producto 1",
            description: "Descripción breve del producton 1",
            price: "340",
        }},
        {{
            image: "https://via.placeholder.com/300",
            title: "Producto 2",
            description: "Descripción breve del producto 2",
            price: "5000",
        }},
        {{
            image: "https://via.placeholder.com/300",
            title: "Producto 3",
            description: "Descripción breve del producto 3",
            price: "{dataBody["price"]}",
        }},
        ];  """

        utils.go_to_main_dir()
        with open(os.getcwd() + "\\" + dataBody["address"] + "\\constants\\body.ts", "w") as file:
            file.write(text)
            file.close()

    @staticmethod
    def modificarSectionInformativa(nombre, address, texto):
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

        utils.go_to_main_dir()
        with open(os.getcwd() + "\\" + address + "\\components\\" + nombre + ".tsx", "w", encoding="utf-8") as file:
            file.write(textSectionNew)

    @staticmethod
    def agregarSectionInformativa(nombre,address,texto):
        #data nombre  y Folder address
        #abrir json de secciones
        #agregar la seccion actual al json
        #y guaradar el json
        #generar una sectionEcommerce pero que devuelva un component con el nombre la nueva section
        #agregar la section a la lista de secciones del navBar

        utils.go_to_main_dir()
        with open(os.getcwd() + "\\" + address + '\\dataSections.json') as file:
            dataSections = json.load(file)
        dataSections.append({"titulo":nombre})
        #guardo json
        with open(os.getcwd() + "\\" + address+"\\dataSections.json", "w") as file:
            file.write(json.dumps(dataSections))
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
        with open(os.getcwd() + "\\" + address+"\\components\\"+nombre+".tsx", "w", encoding="utf-8") as file:
            file.write(textSectionNew)
            
        #genero page
        textPageComponents = ""
        for section in dataSections:
            textPageComponents +=  section["titulo"]+":"+section["titulo"] + ","
        textPageElegibles = ""
        for section in dataSections:
            textPageElegibles += "|" + "\"" + section["titulo"] +"\"" 
        textPageImports = ""
        for section in dataSections:
            textPageImports += "import "+ section["titulo"]  + " from \"../../components/"+section["titulo"]+"\";"
        textPage = f""""use client"
        import Image from "next/image";
        import {{ SearchBar, }} from "../../components";
        import {{ useState }} from "react";
        import {{ NavBar }} from "../../components";
        {textPageImports}

            // Define los posibles valores de mensaje
            type ComponentName = {textPageElegibles};

            // Mapea los nombres de los componentes a los componentes reales
            const componentMap: Record<ComponentName, () => JSX.Element> = {{
            {textPageComponents}
            // Agrega más componentes aquí según sea necesario
            }};

            export default function Home() {{
            const [nombre, setNombre] = useState("Mario");
            const [mensaje, setMensaje] = useState<ComponentName>("SectionECommerce");

            // Cambia la definición de addMensaje para aceptar un argumento de tipo string
            const addMensaje = (mensaje: string) => {{
                console.log(mensaje);
                setMensaje(mensaje as ComponentName); // Convierte el string a ComponentName
            }};

            // Selecciona el componente basado en el valor de `mensaje`
            const SelectedComponent = componentMap[mensaje] || SectionECommerce;

            return (
                <main className="h-full items-center justify-between p-24 w-full">
                <NavBar nombre={{nombre}} addMensaje={{addMensaje}} />
                {{mensaje}}
                <div>
                    {{SelectedComponent ? <SelectedComponent /> : <div>Componente no encontrado</div>}}
                </div>
                </main>
            );
            }}
        """
        with open(os.getcwd() + "\\" + address+"\\src\\app\\page.tsx", "w", encoding="utf-8") as file:
            file.write(textPage)
            
        #genero navBar
        textNavBarSections = ""
        for section in dataSections:
            textNavBarSections += "\"" + section["titulo"] + "\","
        textNavBar = f"""import React from "react";
        import Link from "next/link";
        import {{ NAVIGATION_LINKS }} from "../constants/navbar";

            // Define un tipo para los props de NavBar
            type NavBarProps = {{
            nombre: string;
            addMensaje: (mensaje: string) => void;
            }};

            const NavBar = ({{ nombre, addMensaje }}: NavBarProps) => {{
            const enviarMensaje = () => {{
                addMensaje("childMensaje");
            }};
            const secciones = [
                {textNavBarSections}
            ]
            return (
                <div className="bg-neutral-600 flex items-center justify-between h-10 px-4">
                <nav className="flex flex-grow justify-evenly">
                    {{secciones.map(seccion => (
                    <button key={{seccion}} onClick={{() => addMensaje(seccion)}}>
                        {{seccion}}
                    </button>
                    ))}}
                </nav>
                </div>
            );
            }};

            export default NavBar;

        """
        with open(os.getcwd() + "\\" + address+"\\components\\NavBar.tsx", "w", encoding="utf-8") as file:
            file.write(textNavBar)       