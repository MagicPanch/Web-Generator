"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
const Header = () => {
    return(
        
        <div className=" bg-blue-500 flex  items-center justify-between h-20 px-4">
            <img className="w-20 h-20" src={ "https://png.pngtree.com/png-vector/20220207/ourmid/pngtree-e-letter-logo-ecommerce-shop-store-design-png-image_4381099.png"} alt="Logo"/>
            <h1 className="text-5xl  mb-5  font-semibold text-center flex-1">
                Web ecommerce
            </h1>
        </div>
    )
}
export default Header;
