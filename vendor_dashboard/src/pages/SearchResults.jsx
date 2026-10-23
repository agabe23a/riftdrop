import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, MapPin, Package, ArrowLeft, PlusCircle, Info } from 'lucide-react';
import apiClient from '../api/client';
import { useCart } from '../context/CartContext';

const formatKES = (amount) => {
  return new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(amount);
};

const SearchResults = () => {
  const { search } = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(search);
  const query = queryParams.get('q') || '';

  // Connect to the Global Cart
  const { addToCart } = useCart();

  const [isLoading, setIsLoading] = useState(true);
  const [gpsStatus, setGpsStatus] = useState('Acquiring Location...');
  const [data, setData] = useState({ results: [], impulse_buys: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query) {
      navigate('/');
      return;
    }

    const fetchResults = async (lat, lng) => {
      setGpsStatus('Searching Bomet...');
      try {
        const response = await apiClient.get('/discovery/search', {
          params: { query, user_lat: lat, user_lng: lng, max_distance_km: 5.0 }
        });
        setData(response.data);
      } catch (error) {
        setError(error.response?.data?.detail || "Failed to fetch results. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          fetchResults(position.coords.latitude, position.coords.longitude);
        },
        (err) => {
          console.error(err);
          // Fallback to default Bomet coordinates if GPS is blocked
          fetchResults(-0.7894, 35.3281); 
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      fetchResults(-0.7894, 35.3281);
    }
  }, [query, navigate]);

  const handleAddToCart = (item) => {
    const added = addToCart({
      inventory_id: item.inventory_id,
      name: item.product_name || item.name, 
      price: item.financials ? item.financials.product_price : item.price,
      store_id: item.store_id
    });
    if (!added) setError('Your cart contains items from another store. Complete or clear that cart first.');
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      
      {/* STICKY HEADER */}
      <div className="bg-white shadow-sm sticky top-0 z-50">
        <div className="px-4 py-4 flex items-center space-x-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-full hover:bg-gray-100 transition">
            <ArrowLeft size={24} className="text-gray-700" />
          </button>
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="text-gray-400" size={18} />
            </div>
            <input
              type="text"
              readOnly
              value={query}
              onClick={() => navigate('/')} 
              className="block w-full pl-10 pr-3 py-2 bg-gray-100 rounded-xl border-none text-gray-900 cursor-pointer outline-none"
            />
          </div>
          {/* Cart Icon Link */}
          <button onClick={() => navigate('/checkout')} className="p-2 rounded-full hover:bg-gray-100 transition relative">
             <Package size={24} className="text-gray-700" />
          </button>
        </div>
      </div>

      <div className="p-4">
        {/* LOADING STATE */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="relative w-16 h-16 mb-4">
              <div className="absolute inset-0 border-4 border-gray-200 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-bomet-blue rounded-full border-t-transparent animate-spin"></div>
            </div>
            <h3 className="text-lg font-medium text-gray-900">{gpsStatus}</h3>
          </div>
        )}

        {/* ERROR STATE */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-100 p-4 rounded-2xl text-center">
            <MapPin className="mx-auto text-red-500 mb-2" size={32} />
            <p className="text-red-700 font-medium">{error}</p>
          </div>
        )}

        {/* MAIN RESULTS */}
        {!isLoading && !error && data.results && data.results.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between px-1 mb-2">
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                Fastest & Cheapest
              </h2>
            </div>

            {data.results.map((item, idx) => (
              <div key={item.inventory_id} className={`bg-white rounded-2xl shadow-sm border ${idx === 0 ? 'border-bomet-gold ring-1 ring-bomet-gold' : 'border-gray-100'} p-4 overflow-hidden relative`}>
                
                {idx === 0 && (
                  <div className="absolute top-0 right-0 bg-bomet-gold text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-bl-lg">
                    Best Value
                  </div>
                )}

                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-bold text-gray-900 text-lg">{item.store_name}</h3>
                    <div className="flex items-center text-gray-500 text-xs mt-1 space-x-2">
                      <span className="flex items-center"><MapPin size={12} className="mr-1" /> {item.distance_km} km away</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-xl p-3 mb-4 space-y-2 text-sm border border-gray-100">
                  <div className="flex justify-between text-gray-600">
                    <span>{item.product_name}</span>
                    <span className="font-medium">{formatKES(item.financials.product_price)}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span className="flex items-center">
                      Delivery <Info size={12} className="ml-1 text-gray-400" />
                    </span>
                    <span className="font-medium">{formatKES(item.financials.delivery_fee)}</span>
                  </div>
                </div>

                {/* THE LIVE ADD TO CART BUTTON */}
                <button 
                  onClick={() => handleAddToCart(item)}
                  className="w-full bg-gray-900 text-white font-medium py-3 rounded-xl hover:bg-gray-800 transition shadow-sm"
                >
                  Add to Cart
                </button>
              </div>
            ))}
          </div>
        )}

        {/* IMPULSE BUYS */}
        {!isLoading && !error && data.impulse_buys && data.impulse_buys.length > 0 && (
          <div className="mt-10">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 px-1">
              Perfect With Your Order
            </h2>
            
            <div className="flex overflow-x-auto space-x-4 pb-4 -mx-4 px-4 snap-x">
              {data.impulse_buys.map((upsell) => (
                <div key={upsell.inventory_id} className="snap-start flex-shrink-0 w-40 bg-white border border-gray-100 rounded-2xl p-3 shadow-sm relative">
                  <div className="h-20 bg-orange-50 rounded-lg mb-3 flex items-center justify-center">
                    <PlusCircle className="text-orange-300" size={32} />
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm line-clamp-1">{upsell.product_name}</h4>
                  <p className="text-bomet-green font-bold text-sm mt-1">{formatKES(upsell.price)}</p>
                  
                  {/* UPSELL ADD TO CART BUTTON */}
                  <button 
                    onClick={() => handleAddToCart(upsell)}
                    className="absolute bottom-3 right-3 bg-gray-100 hover:bg-bomet-blue hover:text-white p-2 rounded-full transition-colors text-gray-600"
                  >
                    <PlusCircle size={18} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default SearchResults;
