"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import SearchBar from "./SearchBar";
import ProductTile from "./ProductTile";
const  SectionECommerce = () => {
    return(
        <div>
            
            <div className=" max-w-screen  bg-gray-500  p-4 justify-between h-full px-4">
            <h1 className=" text-2xl  mb-3  font-semibold text-center  p-2 h-full ">
                Compra nuestros productos
            </h1>
            <SearchBar/>
           
           
            <div className="w-full flex justify-center">
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            </div>
            <div className="w-full flex justify-center">
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            </div>
            <div className="w-full flex justify-center">
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            <ProductTile/>
            </div>
            
            </div>
        </div>
    )
        
       
}
export default SectionECommerce;
