import { CartItemInterface } from "../components/cartContext";
import { LINK } from "../constants/link";

export const updateProductQuantities = async (cart: CartItemInterface[]) => {
    try {
        const response = await fetch(LINK + "/api/updateQuantity", {
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