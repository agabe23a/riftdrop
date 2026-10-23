import { useState, useEffect, useCallback } from "react";
import { Search, Plus, Edit, Trash2, Package, X, Loader2 } from "lucide-react";
import apiClient from "../api/client";

const InventoryPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  // State for the API data
  const [masterCatalog, setMasterCatalog] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [inventoryError, setInventoryError] = useState('');
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [selectedProductId, setSelectedProductId] = useState("");
  const [vendorPrice, setVendorPrice] = useState("");
  const [stockQuantity, setStockQuantity] = useState("");

  const storeId = localStorage.getItem('riftdrop_store_id') || 1; // Fallback to 1 for testing

  const fetchStoreInventory = useCallback(async () => {
    if (!storeId) return;
    try {
      const response = await apiClient.get(`/stores/${storeId}/inventory`);
      setInventory(response.data);
    } catch (error) {
      setInventoryError(error.response?.data?.detail || 'Unable to load your inventory.');
    }
  }, [storeId]);

  useEffect(() => { fetchStoreInventory(); }, [fetchStoreInventory]);

  // Fetch the Master Catalog from FastAPI when the modal opens
  useEffect(() => {
    if (isModalOpen) {
      const fetchCatalog = async () => {
        setIsLoadingCatalog(true);
        try {
          const response = await apiClient.get("/catalog/");
          setMasterCatalog(response.data);
        } catch (error) {
          console.error("Failed to fetch catalog:", error);
        } finally {
          setIsLoadingCatalog(false);
        }
      };
      fetchCatalog();
    }
  }, [isModalOpen]);

  // Handle saving the item to the vendor's inventory
  const handleSaveInventory = async () => {
    if (!selectedProductId || !vendorPrice || !stockQuantity) {
      alert("Please select a product and fill in the price and stock.");
      return;
    }

    const finalProductId = parseInt(selectedProductId, 10);
    const finalPrice = parseFloat(vendorPrice);
    const finalStock = parseInt(stockQuantity, 10);

    if (isNaN(finalProductId) || isNaN(finalPrice) || isNaN(finalStock)) {
      alert("System Error: Ensure all fields contain valid numbers.");
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        product_id: finalProductId,
        price: finalPrice, 
        stock_quantity: finalStock,
      };

      await apiClient.post(`/stores/${storeId}/inventory`, payload);

      alert("Product successfully added to your store!");
      await fetchStoreInventory();
      setIsModalOpen(false);

      // Clear inputs for next time
      setSelectedProductId("");
      setVendorPrice("");
      setStockQuantity("");
    } catch (error) {
      console.error("Save failed:", error.response?.data || error.message);
      const errorMsg = error.response?.data?.detail
      ? JSON.stringify(error.response.data.detail)
      : "Failed to save product to inventory.";
      alert(`Error: ${errorMsg}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Inventory Management
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your store's products, pricing, and stock levels.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center justify-center space-x-2 bg-bomet-green hover:bg-green-700 text-white px-4 py-2.5 rounded-lg shadow-sm transition-colors font-medium"
        >
          <Plus size={20} />
          <span>Add New Product</span>
        </button>
      </div>

      {/* Control Bar (Search & Filters) */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="text-gray-400" size={20} />
          </div>
          <input
            type="text"
            placeholder="Search your products..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-bomet-blue focus:border-bomet-blue text-sm transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {inventoryError && <p className="text-sm text-red-600">{inventoryError}</p>}
      
      {/* Data Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price (KES)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {inventory
                .filter((item) => {
                  const productName = item.product?.name || "";
                  return productName.toLowerCase().includes(searchTerm.toLowerCase());
                })
                .map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
                        {item.product?.image_url ? (
                            <img src={item.product.image_url} alt={item.product.name} className="h-full w-full object-cover" />
                        ) : (
                            <Package className="text-gray-400" size={20} />
                        )}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {item.product?.name || "Unknown Product"}
                        </div>
                        <div className="text-xs text-gray-500">
                          Barcode: {item.product?.barcode || "N/A"}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    {item.price.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.stock_quantity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2.5 py-1 inline-flex text-xs font-semibold rounded-full ${item.stock_quantity > 10 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
                    >
                      {item.stock_quantity > 10 ? 'In Stock' : 'Low Stock'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-3">
                      <button className="text-bomet-blue hover:text-blue-800">
                        <Edit size={18} />
                      </button>
                      <button className="text-red-500 hover:text-red-700">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL OVERLAY: Add New Product */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-900">Add Product to Store</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X size={24} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select from Master Catalog</label>
                  {isLoadingCatalog ? (
                    <div className="flex items-center text-sm text-gray-500 py-2">
                      <Loader2 className="animate-spin mr-2 h-4 w-4" /> Loading official products...
                    </div>
                  ) : (
                    <select
                      className="w-full border rounded p-2"
                      value={selectedProductId}
                      onChange={(e) => setSelectedProductId(e.target.value)}
                    >
                      <option value="" disabled>-- Choose a product --</option>
                      {masterCatalog.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  )}
                  <p className="text-xs text-gray-500 mt-1">You must select an official RiftDrop catalog item.</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Your Price (KES)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 250"
                      className="block w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-bomet-blue text-sm"
                      value={vendorPrice}
                      onChange={(e) => setVendorPrice(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Stock Quantity</label>
                    <input
                      type="number"
                      placeholder="e.g. 50"
                      className="block w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-bomet-blue text-sm"
                      value={stockQuantity}
                      onChange={(e) => setStockQuantity(e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-end space-x-3">
              <button
                onClick={() => setIsModalOpen(false)}
                disabled={isSaving}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveInventory}
                disabled={isSaving}
                className="px-4 py-2 flex items-center text-sm font-medium text-white bg-bomet-green hover:bg-green-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
              >
                {isSaving ? (
                  <><Loader2 className="animate-spin mr-2 h-4 w-4" /> Saving...</>
                ) : ("Save to Inventory")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryPage;