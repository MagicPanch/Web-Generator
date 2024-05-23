"use client";
import React, { createContext, useContext, useState, ReactNode } from "react";

export interface ItemInterface {
  image: string;
  title: string;
  description: string;
  price: string;
  key: number;
}

export interface CartItemInterface {
  item: ItemInterface;
  quantity: number;
}

interface CartContextInterface {
  cart: CartItemInterface[];
  addToCart: (item: ItemInterface) => void;
  removeFromCart: (item: ItemInterface) => void;
}

const CartContext = createContext<CartContextInterface | undefined>(undefined);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
};

export const CartProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [cart, setCart] = useState<CartItemInterface[]>([]);

  const addToCart = (item: ItemInterface) => {
    setCart((prevCart) => {
      const existingCartItem = prevCart.find(
        (cartItem) => cartItem.item.key === item.key
      );
      if (existingCartItem) {
        return prevCart.map((cartItem) =>
          cartItem.item.key === item.key
            ? { ...cartItem, quantity: cartItem.quantity + 1 }
            : cartItem
        );
      } else {
        return [...prevCart, { item, quantity: 1 }];
      }
    });
  };

  const removeFromCart = (item: ItemInterface) => {
    setCart((prevCart) => {
      const existingCartItem = prevCart.find(
        (cartItem) => cartItem.item.key === item.key
      );
      if (existingCartItem) {
        if (existingCartItem.quantity > 1) {
          return prevCart.map((cartItem) =>
            cartItem.item.key === item.key
              ? { ...cartItem, quantity: cartItem.quantity - 1 }
              : cartItem
          );
        } else {
          return prevCart.filter((cartItem) => cartItem.item.key !== item.key);
        }
      }
      return prevCart;
    });
  };

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart }}>
      {children}
    </CartContext.Provider>
  );
};
