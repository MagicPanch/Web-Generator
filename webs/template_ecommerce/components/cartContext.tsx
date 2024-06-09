"use client";
import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
} from "react";

export interface ItemInterface {
  multimedia: string;
  name: string;
  desc: string;
  price: string;
  key: number;
  stock: number;
}

export interface CartItemInterface {
  item: ItemInterface;
  quantity: number;
}

interface CartContextInterface {
  cart: CartItemInterface[];
  addToCart: (item: ItemInterface) => void;
  removeFromCart: (item: ItemInterface) => void;
  removeFromCartAll: (item: ItemInterface) => void;
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

  useEffect(() => {
    const storedCart = typeof window !== "undefined" ? localStorage.getItem("cart") : null;
    if (storedCart) {
      setCart(JSON.parse(storedCart));
    }
  }, []);

  const addToCart = (item: ItemInterface) => {
    setCart((prevCart) => {
      const existingCartItem = prevCart.find(
        (cartItem) => cartItem.item.key === item.key
      );

      if (existingCartItem) {
        if (existingCartItem.quantity < existingCartItem.item.stock) {
          return prevCart.map((cartItem) =>
            cartItem.item.key === item.key
              ? { ...cartItem, quantity: cartItem.quantity + 1 }
              : cartItem
          );
        } else {
          alert('No hay suficiente stock disponible');
          return prevCart;
        }
      } else {
        if (item.stock > 0) {
          return [...prevCart, { item, quantity: 1 }];
        } else {
          alert('No hay suficiente stock disponible');
          return prevCart;
        }
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

  const removeFromCartAll = (item: ItemInterface) => {
    setCart((prevCart) => {
      const existingCartItem = prevCart.find(
        (cartItem) => cartItem.item.key === item.key
      );
      if (existingCartItem) {
        return prevCart.filter((cartItem) => cartItem.item.key !== item.key);
      }
      return prevCart;
    });
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("cart", JSON.stringify(cart));
    }
  }, [cart]);

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, removeFromCartAll }}>
      {children}
    </CartContext.Provider>
  );
};

export const AddToCartMessage: React.FC = () => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(true);
  }, []);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 bg-green-500 text-white text-center p-3 z-50 transition-opacity duration-1000 ${
        show ? "opacity-100" : "opacity-0"
      }`}
    >
      ¡Producto agregado al carrito!
    </div>
  );
};
