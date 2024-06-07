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

  // @ts-ignore
  return (
      <div className="bg-gradient-to-b from-customColor-100 to-customColor-900 items-center justify-between p-24 w-full p-4">
        <div style={{filter: blurBackground ? "blur(5px)" : "none"}}>
          <h1 className="text-2xl text-customColor-700 mb-3 font-semibold text-center">
            Carrito de Compras
          </h1>

          {/* Total y Botón de Pago */}
          <div className="text-center mb-4">
            <h3 className="text-2xl text-customColor-700 mb-3 font-semibold">
              Total a pagar: ${totalToPay.toFixed(2)}
            </h3>
            {totalToPay !== 0 && (
                <button
                    onClick={handleCheckout}
                    className="px-4 py-2 rounded-md w-full bg-customColor-500 hover:bg-customColor-600 text-white mb-4"
                >
                  Realizar Pago
                </button>
            )}
          </div>

          {/* Items del Carrito */}
          <div className="flex flex-col items-center py-8">
            <div className="grid gap-y-4 grid-cols-1 justify-center items-center">
              {cart.map((cartItem: CartItemInterface) => (
                  <ProductShoppingTile
                      key={cartItem.item.key}
                      image={cartItem.item.multimedia}
                      title={cartItem.item.name}
                      description={cartItem.item.desc}
                      price={cartItem.item.price}
                      quantity={cartItem.quantity}
                      removeFromCart={() => handleRemoveFromCart(cartItem.item)}
                  />
              ))}
            </div>
          </div>

          {/* Botón de Volver al Menú de Compras */}
          <div className="p-4">
            <Link href="/">
              <button
                  className="px-4 py-2 rounded-md w-full bg-customColor-500 hover:bg-customColor-600 text-white"
              >
                Volver al Menú de Compras
              </button>
            </Link>
          </div>

          {/* Mensaje de eliminación del carrito */}
          {showMessage && <RemoveFromCartMessage/>}
        </div>

        {/* Confirmación de Compra */}
        {showConfirmation && (
            <div
                className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-30"
                style={{top: modalTop ?? 170, right: modalLeft ?? 540}}
            >
              <div className="bg-white p-4 rounded-md text-center shadow-lg border border-black">
                <h2 className="text-xl text-black mb-4">
                  ¡Gracias por comprar en nuestra tienda!
                </h2>
                <h2 className="text-m text-black mb-2">
                  Podrá seguir su envío mediante un link enviado a su e-mail
                </h2>
                <button
                    onClick={handleCloseConfirmation}
                    className="px-4 py-2 rounded-md bg-customColor-500 hover:bg-customColor-600 text-white"
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
    console.log(JSON.stringify({cart}));
    const response = await fetch(LINK + "/api/updateQuantity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({cart}),
    });

    if (!response.ok) {
      throw new Error("Failed to update product quantities");
    }
  } catch (error) {
    console.error("Error updating product quantities:", error);
  }
};