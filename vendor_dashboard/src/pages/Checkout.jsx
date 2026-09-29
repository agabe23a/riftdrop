import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, MapPin, Smartphone, Loader2, ArrowLeft, ShoppingCart } from 'lucide-react';
import apiClient from '../api/client';
import { useCart } from '../context/CartContext';

const formatKES = (amount) => {
  return new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(amount);
};

const Checkout = () => {
  const navigate = useNavigate();
  
  // 1. Pull the live data directly from the Global Cart Engine
  const { cartItems, getCartTotal, clearCart } = useCart();
  
  // 2. Setup state
  const [phone, setPhone] = useState('07');
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState('');
  const [error, setError] = useState('');

  // 3. Dynamic Calculations
  const productTotal = getCartTotal();
  const storeId = cartItems.length > 0 ? cartItems[0].store_id : null;

  const handleCheckout = async (e) => {
    e.preventDefault();
    setError('');
    
    if (cartItems.length === 0) {
      setError("Your cart is empty.");
      return;
    }

    if (phone.length < 10) {
      setError("Please enter a valid phone number (e.g., 0712345678)");
      return;
    }

    if (!storeId) {
      setError("Store information is missing from the cart.");
      return;
    }

    setIsProcessing(true);
    setPaymentStatus('Securing Order & Calculating Delivery...');

    try {
      // Step A: Send Zero-Trust Payload to Backend
      const payload = {
        store_id: storeId,
        phone_number: phone,
        delivery_lat: -0.7894, // In production, we pull this from device GPS
        delivery_lng: 35.3281,
        items: cartItems.map(item => ({
          inventory_id: item.inventory_id,
          quantity: item.quantity
        }))
      };

      const orderResponse = await apiClient.post('/orders/checkout', payload);
      const orderId = orderResponse.data.order_id;
      const amountToPay = orderResponse.data.total_to_pay;

      setPaymentStatus(`Triggering M-Pesa STK Push for KES ${amountToPay}...`);

      // Step B: Trigger M-Pesa STK Push
      await apiClient.post(`/orders/${orderId}/pay`);
      
      setPaymentStatus('Check your phone! Enter your M-Pesa PIN...');
      
      // Step C: Success! Clear the cart and redirect
      setTimeout(() => {
        setIsProcessing(false);
        clearCart(); // Empty the cart because they paid!
        navigate('/'); 
      }, 5000);

    } catch (err) {
      setIsProcessing(false);
      console.error(err);
      setError(err.response?.data?.detail || "Checkout failed. Please try again.");
    }
  };

  // UI State: If the cart is empty, show a warning instead of the payment form
  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <ShoppingCart size={64} className="text-gray-300 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Your Cart is Empty</h2>
        <p className="text-gray-500 mb-6">Looks like you haven't added anything yet.</p>
        <button 
          onClick={() => navigate('/')}
          className="bg-bomet-blue text-white px-6 py-3 rounded-xl font-medium"
        >
          Go Back Shopping
        </button>
      </div>
    );
  }

  // UI State: The actual checkout form
  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="bg-white shadow-sm sticky top-0 z-50 px-4 py-4 flex items-center">
        <button onClick={() => navigate(-1)} className="mr-3 p-2 rounded-full hover:bg-gray-100 transition">
          <ArrowLeft size={24} className="text-gray-700" />
        </button>
        <h1 className="text-xl font-bold text-gray-900">Secure Checkout</h1>
      </div>

      <div className="p-4 space-y-6">
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm font-medium border border-red-100">
            {error}
          </div>
        )}

        {/* ORDER SUMMARY */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Order Summary</h3>
          <div className="space-y-3 mb-4">
            {cartItems.map((item, idx) => (
              <div key={idx} className="flex justify-between text-sm text-gray-700">
                <span>{item.quantity}x {item.name}</span>
                <span className="font-medium">{formatKES(item.price * item.quantity)}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-gray-200 mt-3 pt-3 flex justify-between items-center">
             <span className="text-gray-500 text-sm">Subtotal</span>
             <span className="font-bold text-gray-900">{formatKES(productTotal)}</span>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-right">
            *Rider delivery fee calculated dynamically at next step
          </p>
        </div>

        {/* M-PESA PAYMENT SECTION */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-green-100">
          <div className="flex items-center space-x-2 mb-4">
            <ShieldCheck className="text-green-600" size={24} />
            <h3 className="font-bold text-gray-900">M-Pesa Express</h3>
          </div>

          <form onSubmit={handleCheckout}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              M-Pesa Phone Number
            </label>
            <div className="relative mb-6">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Smartphone className="text-gray-400" size={20} />
              </div>
              <input
                type="tel"
                required
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 outline-none font-medium text-lg tracking-wide"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={isProcessing}
              />
            </div>

            <button
              type="submit"
              disabled={isProcessing}
              className={`w-full flex flex-col justify-center items-center py-4 px-4 rounded-xl shadow-md transition-all ${
                isProcessing ? 'bg-gray-100 text-gray-500' : 'bg-[#46A049] hover:bg-[#3d8c40] text-white'
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="animate-spin h-6 w-6 mb-2 text-green-600" />
                  <span className="font-medium text-center">{paymentStatus}</span>
                </>
              ) : (
                <>
                  <span className="font-bold text-lg">Calculate & Pay</span>
                  <span className="text-xs opacity-80 mt-1">Trigger STK Push</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Checkout;