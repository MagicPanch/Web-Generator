"use client";

import React from "react";

const ProductTile = () => {
    return (
        <div className="bg-white rounded-lg overflow-hidden shadow-md p-4 m-4"> {/* Agrega margen aquí */}
            <img src="https://via.placeholder.com/300" alt="Product" className="w-full" />
            <div className="p-4">
                <h2 className="text-xl font-semibold mb-2">Nombre del Producto</h2>
                <p className="text-gray-600">Descripción breve del producto.</p>
                <div className="mt-4 flex items-center justify-between">
                    <button className="bg-blue-500 text-white px-4 py-2 rounded-md">Comprar</button>
                    <span className="text-gray-600">Precio de $$$</span>
                </div>
            </div>
        </div>
    );
}

export default ProductTile;


