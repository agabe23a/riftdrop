import { createContext, useContext, useState, useEffect } from 'react';

// Create the Context
const CartContext = createContext();

// Create a custom hook so any page can access the cart instantly
export const useCart = () => useContext(CartContext);

export const CartProvider = ({ children }) => {
  // Initialize cart from LocalStorage so users don't lose items on refresh
  const [cartItems, setCartItems] = useState(() => {
    const savedCart = localStorage.getItem('riftdrop_cart');
    return savedCart ? JSON.parse(savedCart) : [];
  });

  // Whenever the cart changes, save it to LocalStorage
  useEffect(() => {
    localStorage.setItem('riftdrop_cart', JSON.stringify(cartItems));
  }, [cartItems]);

  const addToCart = (product) => {
    let added = true;
    setCartItems((prevCart) => {
      if (prevCart.length && prevCart[0].store_id !== product.store_id) {
        added = false;
        return prevCart;
      }
      // Check if the item is already in the cart
      const existingItem = prevCart.find((item) => item.inventory_id === product.inventory_id);
      
      if (existingItem) {
        // If it exists, just increase the quantity
        return prevCart.map((item) =>
          item.inventory_id === product.inventory_id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      
      // If it's new, add it with a quantity of 1
      return [...prevCart, { ...product, quantity: 1 }];
    });
    return added;
  };

  const removeFromCart = (inventory_id) => {
    setCartItems((prevCart) => prevCart.filter((item) => item.inventory_id !== inventory_id));
  };

  const clearCart = () => {
    setCartItems([]);
    localStorage.removeItem('riftdrop_cart');
  };

  // The Financial Calculator
  const getCartTotal = () => {
    return cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getItemCount = () => {
    return cartItems.reduce((count, item) => count + item.quantity, 0);
  };

  return (
    <CartContext.Provider value={{ 
      cartItems, 
      addToCart, 
      removeFromCart, 
      clearCart, 
      getCartTotal, 
      getItemCount 
    }}>
      {children}
    </CartContext.Provider>
  );
};
