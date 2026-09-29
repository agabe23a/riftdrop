import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Package, ShoppingCart, LogOut } from 'lucide-react';

const DashboardLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('riftdrop_token');
    localStorage.removeItem('riftdrop_user');
    navigate('/login');
  };

  const navItems = [
    { name: 'Overview', path: '/vendor', icon: LayoutDashboard },
    { name: 'Inventory', path: '/vendor/inventory', icon: Package },
    { name: 'Live Orders', path: '/vendor/orders', icon: ShoppingCart },
  ];

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      
      {/* RESTORED: Pixel-Perfect Vendor Sidebar */}
      <div className="w-64 bg-[#0F172A] flex flex-col justify-between shadow-xl z-10 border-r border-gray-800">
        <div>
          {/* Brand Header */}
          <div className="p-6 pb-8">
            <h1 className="text-2xl font-bold text-yellow-500 tracking-wide">RiftDrop</h1>
            <p className="text-sm text-gray-400 mt-1">Vendor Portal</p>
          </div>
          
          {/* Navigation Links */}
          <nav className="px-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              // Exact match logic for the active state
              const isActive = location.pathname === item.path || 
                              (item.path !== '/vendor' && location.pathname.startsWith(item.path));
              
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive 
                      ? 'bg-[#1E293B] text-white font-medium shadow-sm' 
                      : 'text-gray-400 hover:bg-[#1E293B] hover:text-white'
                  }`}
                >
                  <Icon size={20} className={isActive ? "text-gray-100" : "text-gray-400"} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sign Out Footer */}
        <div className="p-4 border-t border-gray-800">
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-3 px-4 py-3 w-full text-gray-400 hover:bg-[#1E293B] hover:text-white rounded-lg transition-all"
          >
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Dynamic Content Area */}
      <div className="flex-1 overflow-y-auto bg-[#F8FAFC]">
        <Outlet />
      </div>

    </div>
  );
};

export default DashboardLayout;