import React from "react";

interface CardProps {
  image: string;
  title: string;
  description: string;
  price: string;
}

const ProductTile = ({ image, title, description, price }: CardProps) => {
  return (
    <div className="bg-white rounded-lg overflow-hidden shadow-md p-4 m-4">
      <img src={image} alt="Product" className="w-full" />
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-2">{title}</h2>
        <p className="text-gray-600">{description}</p>
        <div className="mt-4 flex items-center justify-between">
          <button className="bg-blue-500 text-white px-4 py-2 rounded-md">
            Comprar
          </button>
          <span className="text-gray-600">${price}</span>
        </div>
      </div>
    </div>
  );
};

export default ProductTile;
