import { Navigate, Outlet, useLocation } from 'react-router-dom';

const AuthGuard = () => {
  const location = useLocation();
  const token = localStorage.getItem('riftdrop_token');
  
  // We check if this vendor has completed the shop setup
  const isStoreRegistered = localStorage.getItem('riftdrop_store_registered');

  // 1. Not logged in? Kick to login.
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // 2. Logged in, but hasn't registered their shop? Force them to Onboarding.
  // We check location.pathname so we don't cause an infinite redirect loop!
  if (token && !isStoreRegistered && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  // 3. Logged in AND has a store? Let them into the Dashboard.
  return <Outlet />;
};

export default AuthGuard;