import json
import os


class ReactGenerator:

    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ReactGenerator()
        return cls._instance

    def __init__(self) -> None:
        if ReactGenerator._instance is None:
            ReactGenerator._instance = self
        else:
            raise Exception("No se puede crear otra instancia de ReactGenerator")

    @staticmethod
    def generarHeader(data):
        print("genero header")
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
                    <h1 className="text-5xl {data["colorTitulo"]}  mb-5  font-semibold text-center flex-1">
                        {data["titulo"]}
                    </h1>
                </div>
            )
        }}
        export default Header;
        """
        with open(os.getcwd() + "\\" + data["address"]+"\components\Header.tsx", "w") as file:
            file.write(text)
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

        with open(os.getcwd() + "\\" + dataFooter["address"]+"\components\Footer.tsx", "w") as file:
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

        with open(dataBody["address"] + "\constants\/body.ts", "w") as file:
            file.write(text)
            file.close()