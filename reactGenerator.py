
import json

def generarHeader(data):
    print("genero header")
    data = json.loads(data)
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


    with open(data["address"]+"\components\Header.tsx", "w") as file:
        file.write(text)
    with open(data["address"]+"\/tailwind.config.ts", "w") as file:
        file.write(configColor)

def generarFooter(dataFooter):
    print("genero footer")
    dataFooter = json.loads(dataFooter)
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

    with open(dataFooter["address"]+"\constants\/footer.ts", "w") as file:
      file.write(text)

def generarBody(dataBody):
    print("genero body")
    dataBody = json.loads(dataBody)
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

    with open(dataBody["address"]+"\constants\/body.ts", "w") as file:
      file.write(text)

def agregarSectionEcommerce(data):
   #data nombre  y Folder address
   #abrir json de secciones
   #agregar la seccion actual al json
   #y guaradar el json
   #generar una sectionEcommerce pero que devuelva un component con el nombre la nueva section
   #agregar la section a la lista de secciones del navBar
    nombreSection = data["nombre"]
    with open(data["address"]+'/dataSections.json') as file:
        dataSections = json.load(file)
    dataSections.append({"titulo":nombreSection})
    textSections= ""
    for section in dataSections:
        textSections += section+":"+section + ","
    textSectionNew = f"""import React from "react";
    import SearchBar from "./SearchBar";
    import ProductTile from "./ProductTile";
    import {{ CARDS_DATA }} from "../constants/body";

    const {nombreSection} = () => {{
    return (
        <section>
        <div className="max-w-screen bg-blue-300 p-4 h-full px-4">
            <h1 className="text-2xl mb-3 font-semibold text-center p-2 h-full">
            Compra nuestros productos
            </h1>
            <SearchBar />
            <div className="grid gap-y-8 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 py-8 justify-center items-center">
            {{CARDS_DATA &&
                CARDS_DATA.map((item, i) => (
                <ProductTile
                    key={{i}}
                    image={{item.image}}
                    title={{item.title}}
                    description={{item.description}}
                    price={{item.price}}
                />
                ))}}
            </div>
        </div>
        </section>
    );
    }};

    export default {nombreSection};
    """
    with open(data["address"]+"\components\\"+nombreSection+".tsx", "w") as file:
        file.write(textSectionNew)
    textPage = f""" "use client";
    import Image from "next/image";
    import {{ SearchBar, SectionECommerce,SectionInformativa,SectionABM, }} from "../../components";
    import {{ useState }} from "react";
    import {{ NavBar, }} from "../../components";

    // Mapea los nombres de los componentes a los componentes reales
    const componentMap = {{
    SectionECommerce: SectionECommerce,
    SectionInformativa: SectionInformativa,
    SectionABM: SectionABM,
    // Agrega más componentes aquí según sea necesario
    }};

    export default function Home() {{
    
    const [nombre, setNombre]= useState("Mario")
    const [mensaje,setMensaje] = useState("")
    const addMensaje = (mensaje: any) => {{
        console.log(mensaje)
        setMensaje(mensaje);
    }}
    
    const SelectedComponent = componentMap[mensaje] || SectionECommerce;
    return (
        <main className="h-full  items-center justify-between p-24 w-full">
        
        <NavBar nombre={{nombre}} addMensaje={{addMensaje}}/>
        {{mensaje}}
        <div> 
        
        {{SelectedComponent ? <SelectedComponent /> : <div>Componente no encontrado</div>}}
        </div>
        
        </main>
    );
    }}
    """


addres ="C:/Users/Agustin/Desktop/DesingLabel22/Web-Generator/webs/base/base" #direccion donde se ubica la web reactS

dataHeader =  { "titulo": "ecommerce" , "address":addres , "addressLogo": "./logo.png" ,"colorTitulo":"#12D7BF"} 
dataHeader = json.dumps(dataHeader)



dataFooter =  {"address":addres , "email":"contactDesignLabel@gmail.com", "ubicacion": "Pinto 401 Argentina, Tandil"} 
dataFooter = json.dumps(dataFooter)
generarHeader(dataHeader)

dataBody =  {"address":addres , "price":"5000"} 
dataBody = json.dumps(dataBody)

dataSectionEcommerce = {"nombre":"EcommercePrueba","address":addres}
#dataSectionEcommerce = json.dumps(dataSectionEcommerce)
#agregarSectionEcommerce(dataSectionEcommerce)