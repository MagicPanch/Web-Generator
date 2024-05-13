import json

def generarCuerpo(data):
    print("Generando cuerpo...")
    text = f"""
import React from "react";
import Image from "next/image";
import Link from "next/link";
import SearchBar from "./SearchBar";
import ProductTile from "./ProductTile";

const SectionECommerce = () => {{
    const productTiles = [];
    const totalProducts = {data["cantProductos"]};
    const productsPerRow = 4;
    const numRows = Math.ceil(totalProducts / productsPerRow);

    // Generar los ProductTiles
    for (let row = 0; row < numRows; row++) {{
        // Array para los ProductTiles de esta fila
        const rowTiles = [];
        for (let col = 0; col < productsPerRow; col++) {{
            // Calcular el índice en el array total de productos
            const index = row * productsPerRow + col;
            // Verificar si el índice está dentro del rango
            if (index < totalProducts) {{
                rowTiles.push(
                     <div key={{index}} className="relative">
                        <ProductTile />
                    </div>
                    )
            }}
        }}
        // Agregar los ProductTiles de esta fila al array de ProductTiles
        productTiles.push(
            <div key={{row}} className="w-full flex justify-center">
                {{rowTiles}}
            </div>
        );
    }}

    return (
        <div>
            <div className="max-w-screen bg-blue-300 p-4 justify-between h-full px-4">
                <h1 className="text-2xl mb-3 font-semibold text-center p-2 h-full">
                    Compra nuestros productos
                </h1>
                <SearchBar />
                {{/* Renderizar los ProductTiles */}}
                {{productTiles}}
            </div>
        </div>
    );
}}

export default SectionECommerce;
    """
    with open(data["address"] + "\components\SectionECommerce.tsx", "w") as file:
        file.write(text)

address ="C:/Users/Nahu/Desktop/Web-Generator/webs/base/base" #direccion donde se ubica la web react
dataCuerpo = {"cantProductos": "9", "address": address}
dataCuerpo = json.dumps(dataCuerpo)
print(dataCuerpo)
dataDicCuerpo = json.loads(dataCuerpo)
print(dataDicCuerpo["cantProductos"])

generarCuerpo(dataDicCuerpo)
