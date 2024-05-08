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
        with open(data["address"] + "\components\Header.tsx", "w") as file:
            file.write(text)