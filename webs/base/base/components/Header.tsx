"use client";

    import React from "react";
    import logo from './logo.png';
    import Image from "next/image";
    import Link from "next/link";
    
    const Header = () =>  {
        return(
        
            <div className=" bg-blue-500 flex  items-center justify-between h-20 px-4">
                <div className="border-green-300 border-2  rounded h-30 w-30  bg-green-400 items-center">
                    <Image src= {logo}  
                    width={100}
                    height={100}
                    alt="Logo"/>
                </div>
                <h1 className="text-5xl  mb-5  font-semibold text-center flex-1">
                    chau
                </h1>
            </div>
        )
    }
    export default Header;
    