"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
const ProductTile = (data: { titulo: string,descripcion :string}) => {
    return(
        
        <div className=" bg-blue-500 mx-1 my-0.5 rounded border-2 border-white items-center justify-between  px-1  min-h-52 min-w-52">
            <h1 className="text-2xl  mb-2  font-semibold  flex-1">
                {data.titulo}
            </h1>
            <span className="block  mx-0  m-0 text-sm whitespace-normal break-words overflow-hidden text-ellipsis max-h-20">
                
                {data.descripcion} 
            </span>
        </div>
    );
};
export default ProductTile;
