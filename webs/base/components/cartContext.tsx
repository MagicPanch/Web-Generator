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
    // Intenta obtener el carrito desde el almacenamiento local al inicio
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
          // Si el artículo ya está en el carrito y hay suficiente stock, aumenta la cantidad
          return prevCart.map((cartItem) =>
            cartItem.item.key === item.key
              ? { ...cartItem, quantity: cartItem.quantity + 1 }
              : cartItem
          );
        } else {
          // Si no hay suficiente stock, muestra una alerta y retorna el carrito sin cambios
          alert('No hay suficiente stock disponible');
          return prevCart;
        }
      } else {
        if (item.stock > 0) {
          // Si el artículo no está en el carrito y hay stock, añádelo con cantidad 1
          return [...prevCart, { item, quantity: 1 }];
        } else {
          // Si no hay stock disponible, muestra una alerta y retorna el carrito sin cambios
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
    // Guardar el carrito en el almacenamiento local cada vez que cambie
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

export const RemoveFromCartMessage: React.FC = () => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(true);
  }, []);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 bg-red-500 text-white text-center p-3 z-50 transition-opacity duration-1000 ${
        show ? "opacity-100" : "opacity-0"
      }`}
    >
      Producto eliminado del carrito.
    </div>
  );
};