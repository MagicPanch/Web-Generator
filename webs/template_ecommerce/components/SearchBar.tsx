"use client";
import React, { useState } from "react";

interface SearchBarProps {
  onSearch: (term: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = () => {
    onSearch(searchTerm);
  };

  return (
    <div className="flex items-center justify-center mt-4 text-black">
      <input
        type="text"
        className="text-black border border-gray-300 rounded-l-md py-2 px-4 w-3/4 sm:w-1/2 md:w-1/3 lg:w-1/4 focus:outline-none"
        placeholder="Ingrese nombre de producto"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button
        className="bg-customColor-500 hover:bg-customColor-600 text-white font-bold py-2 px-4 rounded-r-md ml-2 focus:outline-none"
        onClick={handleSearch}
      >
        Buscar
      </button>
    </div>
  );
};

export default SearchBar;