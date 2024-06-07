import React from "react";

interface CardProps {
  image: string;
  title: string;
  description: string;
  price: string;
  key: number;
  quantity: number;
  removeFromCart: () => void;
}

const ProductShoppingTile = ({
  image,
  title,
  description,
  price,
  quantity,
  removeFromCart,
}: CardProps) => {
  return (
    <div className="flex flex-row bg-white rounded-lg overflow-hidden shadow-md p-4 m-4">
      <div
        className="flex-shrink-0"
        style={{ width: "180px", height: "180px" }}
      >
        <img src={image} alt="Product" className="w-full h-full object-cover" />
      </div>
      <div className="p-4 flex-1">
        <h2 className="text-xl text-gray-600 font-bold mb-2">{title}</h2>
        <p className="text-gray-600">{description}</p>
        <span className="text-gray-600 font-semibold">${price}</span>
        <p className="text-gray-600 font-semibold mt-4">
          {quantity} unidades seleccionadas
        </p>
        <span className="text-gray-600 font-bold">
          total ${(parseFloat(price) * quantity).toFixed(2)}
        </span>
      </div>
      <button
        onClick={removeFromCart}
        className="bg-customColor-500 hover:bg-customColor-600 text-white px-4 rounded-md self-start"
      >
        Eliminar del carrito
      </button>
    </div>
  );
};

export default ProductShoppingTile;
