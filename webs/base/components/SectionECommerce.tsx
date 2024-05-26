"use client";
import React, { useState } from "react";
import SearchBar from "./SearchBar";
import ProductTile from "./ProductTile";
import { CARDS_DATA } from "../constants/body";
import { AddToCartMessage, ItemInterface, useCart } from "./cartContext";

const SectionECommerce = () => {
  const { addToCart } = useCart();
  const [showAddMessage, setShowAddMessage] = useState(false);

  const handleAddToCart = (item: ItemInterface) => {
    addToCart(item);
    setShowAddMessage(true);
    setTimeout(() => {
      setShowAddMessage(false);
    }, 3000); // Mostrar el mensaje por 3 segundos
  };

  return (
    <section>
      <div className="max-w-screen bg-blue-300 p-4 h-full px-4">
        <h1 className="text-2xl mb-3 font-semibold text-center p-2 h-full">
          Compra nuestros productos
        </h1>
        <SearchBar />
        <div className="grid gap-y-8 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 py-8 justify-center items-center">
          {CARDS_DATA &&
            CARDS_DATA.map((item: ItemInterface) => (
              <ProductTile
                key={item.key}
                image={item.image}
                title={item.title}
                description={item.description}
                price={item.price}
                onAddToCart={() => handleAddToCart(item)}
              />
            ))}
        </div>
      </div>
      {showAddMessage && <AddToCartMessage />}
    </section>
  );
};

export default SectionECommerce;
