import React from "react";

interface CardProps {
  image: string;
  title: string;
  description: string;
  price: string;
  key: number;
  onAddToCart: () => void;
}

const ProductTile = ({
  image,
  title,
  description,
  price,
  onAddToCart,
}: CardProps) => {
  return (
    <div className="bg-white rounded-lg overflow-hidden shadow-md p-4 m-4 transition-transform duration-300 transform hover:scale-105">
      <img src={image} alt="Product" className="w-full" />
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-2">{title}</h2>
        <p className="text-gray-600">{description}</p>
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={onAddToCart}
            className="bg-blue-500 text-white px-4 py-2 rounded-md"
          >
            Agregar al carrito
          </button>
          <span className="text-gray-600">${price}</span>
        </div>
      </div>
    </div>
  );
};

export default ProductTile;
