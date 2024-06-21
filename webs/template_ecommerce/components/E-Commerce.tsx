"use client";

import React, { useState, useEffect } from "react";
import SearchBar from "./SearchBar";
import ProductTile from "./ProductTile";
import { AddToCartMessage, ItemInterface, useCart } from "./cartContext";
import { LINK } from "../constants/link";

let messageTimer: NodeJS.Timeout;

const SectionECommerce: React.FC = () => {
  const { addToCart } = useCart();
  const [showMessage, setShowMessage] = useState(false);
  const [products, setProducts] = useState<ItemInterface[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await fetch(`${LINK}/api?search=${searchTerm}`);
        const productsData = await res.json();
        console.log("Fetched products:", productsData);
        if (Array.isArray(productsData)) {
          setProducts(productsData);
        } else {
          console.error("Fetched data is not an array:", productsData);
          setProducts([]); // O maneja este caso adecuadamente
      }
      } catch (error) {
        console.error("Error fetching products:", error);
        setProducts([]); // O maneja este caso adecuadamente
      }
    };

    fetchProducts();
  }, [searchTerm]);

  const handleAddToCart = (item: ItemInterface) => {
    addToCart(item);
    setShowMessage(true);
    clearTimeout(messageTimer);
    messageTimer = setTimeout(() => {
      setShowMessage(false);
    }, 1500);
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
  };

  return (
    <section>
      <div className="bg-h-screen bg-gradient-to-b from-customColor-100 to-customColor-900 p-4 h-full px-4">
        <h1 className="text-2xl text-customColor-700 mb-3 font-semibold text-center p-2 h-full">
          Compra nuestros productos
        </h1>
        <SearchBar onSearch={handleSearch} />
        <div className="grid gap-y-8 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 py-8 justify-center items-center">
          {products &&
            products.map((item: ItemInterface) => (
              <ProductTile
                key={item.key}
                image={item.multimedia}
                title={item.name}
                description={item.desc}
                price={item.price}
                stock={item.stock}
                onAddToCart={() => handleAddToCart(item)}
              />
            ))}
        </div>
      </div>
      {showMessage && <AddToCartMessage />}
    </section>
  );
};

export default SectionECommerce;