import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, MapPin, Tag, Loader2, Navigation } from 'lucide-react';
import apiClient from '../api/client';

const StoreOnboarding = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState('');
  
  // Real production state structure
  const [formData, setFormData] = useState({
    name: '',
    categoryId: 1, // Will map to your real DB categories
    latitude: null,
    longitude: null
  });

  // The GPS Engine
  const captureLocation = (e) => {
    e.preventDefault(); // Prevent form submission
    setIsLocating(true);
    setError('');

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData({
            ...formData,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
          setIsLocating(false);
        },
        (err) => {
          console.error(err);
          setError("Location access denied. Riders need your exact coordinates to pick up orders.");
          setIsLocating(false);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      setError("Your device does not support GPS location.");
      setIsLocating(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.latitude || !formData.longitude) {
      setError("You must capture your GPS location before continuing.");
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      // REAL API CALL: We will build this backend route next!
      const response = await apiClient.post('/stores/', {
        name: formData.name,
        category_id: parseInt(formData.categoryId),
        latitude: formData.latitude,
        longitude: formData.longitude
      });
      
      // Update the AuthGuard that this vendor now has a store
      localStorage.setItem('riftdrop_store_registered', 'true');
      // Store their new physical store ID so we never have to hardcode "storeId = 1" again
      localStorage.setItem('riftdrop_store_id', response.data.id);
      
      navigate('/'); 
      
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to register store. Backend route missing.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bomet-gray flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden">
        
        <div className="bg-bomet-dark p-6 text-center border-b-4 border-bomet-gold">
          <h2 className="text-2xl font-bold text-white tracking-wide">Register Your Shop</h2>
          <p className="text-gray-400 text-sm mt-1">Pin your exact location for Bodaboda pickups</p>
        </div>

        <div className="p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            
            {/* Shop Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Shop Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Store className="text-gray-400" size={20} />
                </div>
                <input
                  type="text"
                  required
                  placeholder="e.g., K-Matt Supermarket"
                  className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bomet-blue outline-none text-sm"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
            </div>

            {/* Shop Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Primary Category</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Tag className="text-gray-400" size={20} />
                </div>
                {/* We map to IDs so the backend can link it relationally */}
                <select
                  className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bomet-blue outline-none bg-white text-sm"
                  value={formData.categoryId}
                  onChange={(e) => setFormData({...formData, categoryId: e.target.value})}
                >
                  <option value={1}>Grocery & Food</option>
                  <option value={2}>Electronics & Gadgets</option>
                  <option value={3}>Fashion & Apparel</option>
                  <option value={4}>Hardware & Agrovets</option>
                </select>
              </div>
            </div>

            {/* GPS Location Capture */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Store GPS Coordinates</label>
              
              {formData.latitude ? (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
                  <div>
                    <span className="font-semibold block">Location Secured</span>
                    <span className="text-xs">Lat: {formData.latitude.toFixed(4)}, Lng: {formData.longitude.toFixed(4)}</span>
                  </div>
                  <button onClick={captureLocation} className="text-green-600 underline text-xs">Update</button>
                </div>
              ) : (
                <button
                  onClick={captureLocation}
                  disabled={isLocating}
                  className="w-full flex items-center justify-center space-x-2 py-3 px-4 border-2 border-dashed border-gray-300 rounded-lg text-sm font-medium text-gray-600 hover:border-bomet-blue hover:text-bomet-blue transition-colors disabled:opacity-50"
                >
                  {isLocating ? (
                    <><Loader2 className="animate-spin h-5 w-5" /> <span>Acquiring Satellites...</span></>
                  ) : (
                    <><Navigation size={20} /> <span>Tap to Pin GPS Location</span></>
                  )}
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || !formData.latitude}
              className="w-full flex justify-center items-center py-3 px-4 rounded-lg shadow-sm text-sm font-medium text-white bg-bomet-green hover:bg-green-700 transition-colors mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <><Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" /> Securing Store...</>
              ) : (
                'Initialize Storefront'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default StoreOnboarding;