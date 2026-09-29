import { useState, useEffect, useRef } from 'react';
import { ShoppingCart, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const LiveOrders = () => {
  const [orders, setOrders] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const ws = useRef(null);

  // In production, we pull the exact store_id and token from Auth context/localStorage
  const userString = localStorage.getItem('riftdrop_user');
  const storeId = localStorage.getItem('riftdrop_store_id');
  const token = localStorage.getItem('riftdrop_token');

  useEffect(() => {
    if (!storeId || !token) {
      setConnectionStatus('Authentication Error');
      return;
    }

    // Connect directly to your FastAPI WebSocket endpoint
    // Adjust the ws:// URL if your backend runs on a different port/IP
    const wsUrl = `ws://127.0.0.1:8000/api/v1/logistics/ws/vendor/${storeId}?token=${token}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setConnectionStatus('Live: Monitoring Incoming Orders');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Listen specifically for the NEW_PAID_ORDER event your backend broadcasts
      if (data.event === 'NEW_PAID_ORDER') {
        // Add the new order to the top of the list dynamically
        setOrders((prevOrders) => [
          {
            id: data.order_id,
            cart_total: data.cart_total,
            status: 'PENDING_PACKING',
            timestamp: new Date().toLocaleTimeString(),
          },
          ...prevOrders
        ]);
        
        // Optional: Play a "ding" sound here to alert the vendor
      }
    };

    ws.current.onclose = () => {
      setConnectionStatus('Disconnected. Reconnecting...');
      // A Senior system implements exponential backoff reconnection logic here
    };

    // Cleanup the connection when the vendor leaves the page
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [storeId, token]);

  const acceptOrder = (orderId) => {
    // We will wire this to a POST request later to change order status to ACCEPTED
    setOrders(orders.map(o => o.id === orderId ? { ...o, status: 'PACKING' } : o));
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Orders</h1>
          <p className="text-gray-500 mt-1">Accept and pack orders in real-time.</p>
        </div>
        
        {/* Connection Status Indicator */}
        <div className={`flex items-center px-4 py-2 rounded-full text-sm font-medium border ${
          connectionStatus.includes('Live') 
            ? 'bg-green-50 text-green-700 border-green-200' 
            : 'bg-yellow-50 text-yellow-700 border-yellow-200'
        }`}>
          <span className={`w-2 h-2 rounded-full mr-2 ${connectionStatus.includes('Live') ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></span>
          {connectionStatus}
        </div>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
          <ShoppingCart size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">Awaiting Orders</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Your store is online. When a customer completes an M-Pesa payment, the order will appear here instantly.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {orders.map((order) => (
            <div key={order.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex justify-between items-center transition-all hover:shadow-md">
              <div className="flex items-center space-x-6">
                <div className="bg-blue-50 text-bomet-blue p-4 rounded-xl text-center min-w-[80px]">
                  <p className="text-xs font-bold uppercase tracking-wider mb-1">Order</p>
                  <p className="text-xl font-black">#{order.id}</p>
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-lg">Value: KES {order.cart_total}</h3>
                  <div className="flex items-center text-sm text-gray-500 mt-1 space-x-4">
                    <span className="flex items-center"><Clock size={14} className="mr-1" /> {order.timestamp}</span>
                    <span className={`flex items-center font-medium ${order.status === 'PACKING' ? 'text-blue-600' : 'text-orange-500'}`}>
                      <AlertCircle size={14} className="mr-1" /> {order.status}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                {order.status === 'PENDING_PACKING' ? (
                  <button 
                    onClick={() => acceptOrder(order.id)}
                    className="bg-bomet-green hover:bg-green-700 text-white font-medium px-6 py-3 rounded-lg transition-colors shadow-sm"
                  >
                    Accept & Pack
                  </button>
                ) : (
                  <button disabled className="bg-gray-100 text-gray-500 font-medium px-6 py-3 rounded-lg flex items-center cursor-not-allowed">
                    <CheckCircle size={18} className="mr-2 text-green-500" /> Packing
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LiveOrders;