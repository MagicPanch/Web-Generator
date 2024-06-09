"use client";

import React, { useState } from "react";
import logo from './logo.png';
import Image from "next/image";
import { SECTIONS } from "../constants/sections";
import { useCart } from "./cartContext";
import { updateProductQuantities } from "../utils/updateProductQuantities";

type HeaderProps = {
  currentSection: string;
  setSection: (section: string) => void;
};

const Header = ({ currentSection, setSection }: HeaderProps) => {
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const { cart, removeFromCart, removeFromCartAll } = useCart();

  const toggleCart = () => setIsCartOpen(!isCartOpen);

  const handleCheckout = async () => {
    try {
      // Cerrar el carrito
      setIsCartOpen(false);
      // Vaciar el carrito
      cart.forEach((cartItem) => { removeFromCartAll(cartItem.item); cartItem.item.stock -= cartItem.quantity});
      // Actualizar DB
      await updateProductQuantities(cart);
      // Mostrar la ventana de confirmación
      setShowConfirmation(true);
    } catch (error) {
      console.error("Error during checkout:", error);
      // Manejar errores (puedes mostrar un mensaje de error aquí)
    }
  };


  const closeConfirmation = () => {
    setShowConfirmation(false);
  };

  return (
    <div className="bg-customColor-500 flex items-center h-20 px-4 justify-between">
      <div className="relative h-full flex items-center">
        <Image
          src={logo}
          alt="Logo"
          layout="fixed"
          objectFit="contain"
          width={100}
          height={100}
          style={{ maxHeight: "100%", height: "auto", width: "auto" }}
        />
      </div>
      <nav className="flex flex-grow items-center ml-4">
        {SECTIONS.map((section) => (
          <button
            key={section.name}
            className={`mx-2 px-4 py-2 rounded ${
              currentSection === section.name
                ? 'bg-customColor-700 text-white font-bold'
                : 'hover:bg-customColor-600 text-white'
            }`}
            onClick={() => setSection(section.name)}
          >
            {section.name.replace("Section", "")}
          </button>
        ))}
      </nav>
      <div>
        <button
          className="bg-white rounded-full p-2 shadow-md hover:bg-customColor-50"
          onClick={toggleCart}
        >
          <span className="text-customColor-800">🛒 ({cart.length})</span>
        </button>
      </div>

      {isCartOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-end items-center">
          <div className="bg-white p-4 rounded-lg shadow-lg w-96 h-full overflow-auto z-50">
            <h2 className="text-xl text-customColor-700 mb-4">Carrito de Compras</h2>
            {cart.length === 0 ? (
              <p className="text-center">Aún no agregaste productos al carrito.</p>
            ) : (
              <div>
                {cart.map((cartItem) => (
                  <div key={cartItem.item.key} className="flex items-center mb-4">
                    <img src={cartItem.item.multimedia} alt={cartItem.item.name} className="w-24 h-24 object-cover rounded mr-4" />
                    <div>
                      <h3 className="text-lg text-customColor-700">{cartItem.item.name}</h3>
                      <p className="text-gray-600">Precio: ${cartItem.item.price}</p>
                      <p className="text-gray-600">Cantidad: {cartItem.quantity}</p>
                      <button
                        className="text-red-500 hover:underline"
                        onClick={() => { removeFromCart(cartItem.item) } }
                          >
                        Eliminar
                      </button>
                    </div>
                  </div>
                ))}
                <div className="mt-4">
                  <h3 className="text-xl text-customColor-700">Total a pagar: ${cart.reduce((acc, item) => acc + parseFloat(item.item.price) * item.quantity, 0).toFixed(2)}</h3>
                  <button
                    className="mt-4 bg-customColor-500 text-white px-4 py-2 rounded hover:bg-customColor-600"
                    onClick={handleCheckout}
                  >
                    Realizar Pago
                  </button>
                </div>
              </div>
            )}
            <button
              className="mt-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              onClick={toggleCart}
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center">
            <h2 className="text-xl text-customColor-700 mb-4">¡Gracias por comprar en nuestra tienda!</h2>
            <button
              className="bg-customColor-500 text-white px-4 py-2 rounded hover:bg-customColor-600"
              onClick={closeConfirmation}
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Header;