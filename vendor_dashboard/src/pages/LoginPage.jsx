import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, Mail, AlertCircle, Loader2 } from "lucide-react";
import apiClient from "../api/client";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // Send the payload to our FastAPI backend
      const formData = new URLSearchParams();
      formData.append("username", email); // Must be 'username' for OAuth2
      formData.append("password", password);

      const response = await apiClient.post("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      
      const user = response.data.user;


      // If successful, save the JWT token and user data to LocalStorage
      localStorage.setItem("riftdrop_token", response.data.access_token);
      localStorage.setItem("riftdrop_user", JSON.stringify(response.data.user));

      // Redirect to the Dashboard Overview
      if (user.role === 'RIDER') {
        navigate('/rider');
      } else {
        navigate('vendor');    
      }
    } catch (err) {
      // Handle the strict 401 or 403 errors we built in the backend
      if (err.response && err.response.data) {
        setError(err.response.data.detail);
      } else {
        setError("Network error. Is the RiftDrop backend running?");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bomet-gray flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header Section */}
        <div className="bg-bomet-dark p-8 text-center">
          <h1 className="text-4xl font-bold text-bomet-gold tracking-wider mb-2">
            RiftDrop
          </h1>
          <p className="text-gray-300">Vendor Management Portal</p>
        </div>

        {/* Form Section */}
        <div className="p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
            Welcome Back
          </h2>

          {/* Error Alert Box */}
          {error && (
            <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 flex items-start space-x-3 rounded-r-md">
              <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={20} />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="text-gray-400" size={20} />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bomet-blue focus:border-bomet-blue transition-colors sm:text-sm"
                  placeholder="vendor@bomet.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="text-gray-400" size={20} />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bomet-blue focus:border-bomet-blue transition-colors sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-bomet-green hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-bomet-green transition-colors disabled:opacity-70 disabled:cursor-not-allowed mt-4"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                  Authenticating...
                </>
              ) : (
                "Secure Login"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Protected by RiftDrop Enterprise Security
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
