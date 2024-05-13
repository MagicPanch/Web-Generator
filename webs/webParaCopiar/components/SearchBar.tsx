"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
const SearchBar = () => {
    return(
        
        <div className="  flex  w-full items-center justify-between h-10 px-4">
            <input
                type="text"
                className="border w-full border-gray-300 p-2 rounded text-black"
                placeholder= "ingrese nombre de producto"
                //onChange={handleChange}
                //value={inputValue}
            />
        </div>
        
    )
}
export default SearchBar;
