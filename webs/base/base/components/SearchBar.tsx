"use client";

import React from "react";

const SearchBar = () => {
    return (
        <div className="flex items-center justify-center mt-4">
            <input
                type="text"
                className="border border-gray-300 rounded-l-md py-2 px-4 w-3/4 sm:w-1/2 md:w-1/3 lg:w-1/4 focus:outline-none"
                placeholder="Ingrese nombre de producto"
            />
            <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-r-md ml-2 focus:outline-none">
                Buscar
            </button>
        </div>
    );
}

export default SearchBar;

