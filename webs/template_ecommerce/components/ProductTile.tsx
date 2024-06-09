import React from "react";

interface CardProps {
  image: string;
  title: string;
  description: string;
  price: string;
  key: number;
  stock: number;
  onAddToCart: () => void;
}

const ProductTile = ({
  image,
  title,
  description,
  price,
  stock,
  onAddToCart,
}: CardProps) => {
  return (
      <div className="bg-white rounded-lg overflow-hidden shadow-md p-4 m-4 transition-transform duration-300 transform hover:scale-105">
        <img src={image} alt="Product" className="w-full h-full object-cover"/>
        <div className="p-4 h-48 flex flex-col justify-between">
          <h2 className="text-xl font-bold mb-2 text-customColor-800">{title}</h2>
          <p className="text-lg text-gray-600 flex-grow">{description}</p>
          <p className="text-customColor-800 flex-grow">Stock disponible: {stock} unidades.</p>
          <div className="mt-4 flex items-center justify-between">
            <span className="font-semibold text-xl text-customColor-800">${price}</span>
            <button
                onClick={onAddToCart}
                className="bg-customColor-500 hover:bg-customColor-600 text-white px-3 py-2 rounded-md"
            >
              Agregar al carrito
            </button>
          </div>
        </div>
      </div>
  );
};

export default ProductTile;
