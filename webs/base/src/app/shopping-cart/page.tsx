"use client";
import React from "react";
import { CartItemInterface, useCart } from "../../../components/cartContext";
import ProductShoppingTile from "./ProductShoppingTile";
import Link from "next/link";

const ShoppingCart: React.FC = () => {
  const { cart, removeFromCart } = useCart();

  const totalToPay = cart.reduce((acc, cartItem) => {
    return acc + parseFloat(cartItem.item.price) * cartItem.quantity;
  }, 0);

  return (
    <div className="bg-blue-300 p-4">
      <h1 className="text-2xl mb-3 font-semibold text-center">
        Carrito de Compras
      </h1>
      <div className="grid gap-y-8 grid-cols-1 py-8 justify-center items-center">
        {cart.map((cartItem: CartItemInterface) => (
          <ProductShoppingTile
            key={cartItem.item.key}
            image={cartItem.item.image}
            title={cartItem.item.title}
            description={cartItem.item.description}
            price={cartItem.item.price}
            quantity={cartItem.quantity}
            removeFromCart={() => removeFromCart(cartItem.item)}
          />
        ))}
      </div>
      <h3 className="text-2xl mb-3 font-semibold text-center">
        Total a pagar: ${totalToPay.toFixed(2)}
      </h3>

      {totalToPay !== 0 ? (
        <button
          //onClick={}
          className={"px-4 py-2 rounded-md w-full bg-blue-500 text-white"}
        >
          Realizar Pago
        </button>
      ) : (
        <Link href="/">
          <button
            className={"px-4 py-2 rounded-md w-full bg-blue-500 text-white"}
          >
            Volver al Menú de Compras
          </button>
        </Link>
      )}
    </div>
  );
};

export default ShoppingCart;
