
import json

def generarHeader(data):
    print("genero header")
    text = f""""use client";

    import React from "react";
    import logo from './logo.png';
    import Image from "next/image";
    import Link from "next/link";

    const Header = () =>  {{
        return(
        
            <div className=" bg-blue-500 flex  items-center justify-between h-20 px-4">
                <div className="border-green-300 border-2  rounded h-30 w-30  bg-green-400 items-center">
                    <Image src= {{{data["addresImg"]}}}  
                    width={{100}}
                    height={{100}}
                    alt="Logo"/>
                </div>
                <h1 className="text-5xl  mb-5  font-semibold text-center flex-1">
                    {data["titulo"]}
                </h1>
            </div>
        )
    }}
    export default Header;
    """
    with open(data["address"]+"\components\Header.tsx", "w") as file:
        file.write(text)



addres ="C:/Users/Agustin/Desktop/DesingLabelBranchSanti/Web-Generator/webs/base/base" #direccion donde se ubica la web react
dataHeader =  { "titulo": " holar reinas" , "address":addres , "addresImg": "logo"} 
dataHeader = json.dumps(dataHeader)
print(dataHeader)
dataDicHeader = json.loads(dataHeader)
print(dataDicHeader["titulo"])

generarHeader(dataDicHeader)