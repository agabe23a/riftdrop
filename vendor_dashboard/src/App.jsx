import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthGuard from './components/AuthGuard';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import InventoryPage from './pages/InventoryPage';
import StoreOnboarding from './pages/StoreOnboarding';
import CustomerHome from './pages/CustomerHome';
import SearchResults from './pages/SearchResults';
import Checkout from './pages/Checkout';
import { CartProvider } from './context/CartContext';
import LiveOrders from './pages/LiveOrders';
import RiderRadar from './pages/RiderRadar';

const OverviewPage = () => <div className="p-6"><div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">Welcome to your RiftDrop Dashboard.</div></div>;
const OrdersPage = () => <div className="p-6"><div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">Live Orders Coming Soon</div></div>;

function App() {
  return (
    <CartProvider>
      <BrowserRouter>
        <Routes>
          
          {/* =========================================
              DOMAIN 1: THE CUSTOMER APP (Public)
              No sidebar, fully mobile optimized
              ========================================= */}
          <Route path="/" element={<CustomerHome />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/checkout" element={<Checkout />} />

          {/* =========================================
              DOMAIN 2: VENDOR AUTH & ONBOARDING
              ========================================= */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* PROTECTED ROUTES (Requires JWT Token) */}
          <Route element={<AuthGuard />}>
            <Route path="/onboarding" element={<StoreOnboarding />} />


            {/* =========================================
    DOMAIN 3: THE RIDER DISPATCH APP
    Strictly mobile-focused, dark mode radar
    ========================================= */}
      <Route path="/rider" element={<AuthGuard />}>
      <Route index element={<RiderRadar />} />
     </Route>

            
            {/* 
              All dashboard routes are now prefixed with /vendor
              to prevent collisions with the Customer UI 
            */}
            <Route path="/vendor" element={<DashboardLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route element={<LiveOrders />} path="orders" />
            </Route>
          </Route>

          {/* CATCH-ALL (404) */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </CartProvider>
  );
}

export default App;