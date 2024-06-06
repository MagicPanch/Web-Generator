"use client";
import React, { useState, useEffect } from "react";
import {
  CartItemInterface,
  ItemInterface,
  RemoveFromCartMessage,
  useCart,
} from "../../../components/cartContext";
import ProductShoppingTile from "./ProductShoppingTile";
import Link from "next/link";
import{LINK} from "../../../constants/link"
import { Console } from "console";

let messageTimer: NodeJS.Timeout;

const ShoppingCart: React.FC = () => {
  const { cart, removeFromCart,removeFromCartAll } = useCart();
  const [showMessage, setShowMessage] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [modalTop, setModalTop] = useState<number | null>(null);
  const [modalLeft, setModalLeft] = useState<number | null>(null);
  const [blurBackground, setBlurBackground] = useState(false); // State para controlar el efecto de desenfoque


  useEffect(() => {
    if (showConfirmation) {
      document.body.style.overflow = "hidden";
      setBlurBackground(true); // Aplicar desenfoque al fondo
    } else {
      document.body.style.overflow = "auto";
      setBlurBackground(false); // Quitar desenfoque al fondo
    }
  }, [showConfirmation]);

  const handleRemoveFromCart = (item: ItemInterface) => {
    removeFromCart(item);
    setShowMessage(true);
    clearTimeout(messageTimer);
    messageTimer = setTimeout(() => {
      setShowMessage(false);
    }, 1500);
  };

  const handleCheckout = () => {
    setShowConfirmation(true);
  };

  const handleCloseConfirmation = async () => {
    setShowConfirmation(false);

    await updateProductQuantities(cart);
    // Eliminar todos los elementos del carrito al cerrar la confirmación de compra
    cart.forEach((cartItem) => {
      removeFromCartAll(cartItem.item);
    });
    // Redirigir al menú de compras
    window.location.href = "/";
  };

  useEffect(() => {
    const firstCartItem = document.getElementById("firstCartItem");
    if (firstCartItem) {
      const { top, left } = firstCartItem.getBoundingClientRect();
      setModalTop(top - 100); // Ajusta la posición del modal 100px arriba del primer producto en el carrito
      setModalLeft(left - 100);
    }
  }, [cart]);

  const totalToPay = cart.reduce((acc, cartItem) => {
    return acc + parseFloat(cartItem.item.price) * cartItem.quantity;
  }, 0);

  return (
    <div className="bg-blue-300 p-4">
      <div style={{ filter: blurBackground ? "blur(5px)" : "none" }}> {/* Aplica el estilo de desenfoque si blurBackground es true */}
        <h1 className="text-2xl mb-3 font-semibold text-center">
          Carrito de Compras
        </h1>
        <div className="grid gap-y-4 grid-cols-1 py-8 justify-center items-center">
          {cart.map((cartItem: CartItemInterface, index) => (
            <ProductShoppingTile
              key={cartItem.item.key}
              //id={index === 0 ? "firstCartItem" : undefined} // Marca el primer elemento del carrito
              image={cartItem.item.multimedia}
              title={cartItem.item.name}
              description={cartItem.item.desc}
              price={cartItem.item.price}
              quantity={cartItem.quantity}
              removeFromCart={() => handleRemoveFromCart(cartItem.item)}
            />
          ))}
        </div>
        <h3 className="text-2xl mb-3 font-semibold text-center">
          Total a pagar: ${totalToPay.toFixed(2)}
        </h3>

        {totalToPay !== 0 ? (
          <button
            onClick={handleCheckout}
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
        {showMessage && <RemoveFromCartMessage />}
      </div>
      {showConfirmation && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-30"
          style={{ top: modalTop ?? 170, right: modalLeft ?? 540 }}
        >
          <div className="bg-white p-4 rounded-md text-center shadow-lg border border-black">
            <h2 className="text-xl text-black mb-4">
              Felicitaciones por su compra!!!
            </h2>
            <h2 className="text-m text-black mb-2">
              Podrá seguir su envío mediante un link enviado a su e-mail
            </h2>
            <button
              onClick={handleCloseConfirmation}
              className="px-4 py-2 rounded-md bg-blue-500 text-white"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShoppingCart;

const updateProductQuantities = async (cart: CartItemInterface[]) => {
  try {
    console.log(JSON.stringify({ cart }));
    const response = await fetch(LINK+"/api/updateQuantity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ cart }),
    });

    if (!response.ok) {
      throw new Error("Failed to update product quantities");
    }
  } catch (error) {
    console.error("Error updating product quantities:", error);
  }
};