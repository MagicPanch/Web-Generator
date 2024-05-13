"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import SearchBar from "./SearchBar";
import ProductTile from "./ProductTile";
const  SectionECommerce = () => {
    const productData1 = {titulo : "titulo",descripcion: "soy una descripcion"}
    const productos =[ {titulo:"Mesa",descripcion:"Excelente mesa de alta madera"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"}
    ,{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"},{titulo:"tilo2",descripcion:"d2"}
    ]
    return(
        <div>
            
            <div className=" max-w-screen bg-gray-500  p-4 justify-between h-full px-4">
            <h1 className=" text-2xl  mb-3  font-semibold text-center  p-2 h-full max-w-3/4 ">
                Compra nuestros productos
            </h1>
            <div className="flex justify-center">
            <div className="w-3/4 ">
                <SearchBar/>
            </div>
            </div>
           
            
           
           
            <div className="w-full my-5 flex flex-wrap justify-center  gap-1 justify-items-center">
            {/* <ProductTile titulo="producto A" descripcion="El producto a1 es una verdadera maravilla de la creatividad"/> */}
            {/*<ProductTile {...productData1} /> */}
            {/*<ProductTile titulo="producto A" descripcion="d1"/> */}
            
            {productos.map((producto, index) => (
                 <ProductTile key={index} {...producto} />  
            ))}
            </div>
            
            
            </div>
        </div>
    )
        
       
}
export default SectionECommerce;
