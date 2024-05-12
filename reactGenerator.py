
import json

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
    with open(data["address"]+"\components\Header.tsx", "w") as file:
        file.write(text)

def generarFooter(dataDicFooter):
    print("genero footer")
    dataDicFooter = json.loads(dataDicFooter) 
    text = f""""

    export const FOOTER_LINKS = [
  {{
    title: "Navegación",
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
    {{ label: "Email", value: {dataDicFooter["email"]} }},
    {{ label: "Ubicación", value: {dataDicFooter["ubicacion"]} }},
  ],
}};

export const SOCIALS = {{
  title: "Social",
  data: [
    {{
      image: "/facebook.svg",
      href: "https://www.facebook.com",
    }},
    {{ image: "/instagram.svg", href: "https://www.instagram.com" }},
    {{ image: "/x.svg", href: "https://twitter.com" }},
  ],
}};
    """

    with open(dataDicFooter["address"]+"\constants\footer.ts", "w") as file:
      file.write(text)


addres ="C:/Users/Agustin/Desktop/DesingLabelBranchSanti/Web-Generator/webs/base/base" #direccion donde se ubica la web react
dataHeader =  { "titulo": "ecommerce" , "address":addres , "addressLogo": "./logo.png" ,"colorTitulo":"text-yellow-600"} 
dataHeader = json.dumps(dataHeader)
print(dataHeader)
dataDicHeader = json.loads(dataHeader)
print(dataDicHeader["titulo"])

dataFooter =  {"address":addres , "email":"contactDesignLabel@gmail.com", "ubicacion": "Pinto 400 Argentina, Tandil"} 
dataFooter = json.dumps(dataFooter)
generarFooter(dataFooter)