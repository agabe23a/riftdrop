import { Outlet } from 'react-router-dom';
// Import your Vendor Sidebar component here
// import VendorSidebar from '../components/VendorSidebar'; 

const VendorLayout = () => {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* 1. The strict Vendor Sidebar goes here */}
      {/* <VendorSidebar /> */}
      
      {/* 2. The main dashboard content renders inside the Outlet */}
      <div className="flex-1 overflow-y-auto">
        <Outlet /> 
      </div>
    </div>
  );
};

export default VendorLayout;