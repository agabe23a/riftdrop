import { useState, useEffect } from "react";
import { Search, Sun, Moon, Coffee, Navigation } from "lucide-react";
import { useNavigate } from "react-router-dom";

const CustomerHome = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [context, setContext] = useState(null);

  // THE SMART CONTEXT ENGINE
  useEffect(() => {
    const hour = new Date().getHours();

    if (hour >= 5 && hour < 11) {
      setContext({
        greeting: "Good Morning!",
        subtext: "Need quick breakfast before class?",
        icon: <Coffee className="text-bomet-gold" size={28} />,
        bgGradient: "from-orange-100 to-yellow-50",
        smartTags: ["Milk", "Bread", "Eggs", "Tea Leaves"],
      });
    } else if (hour >= 11 && hour < 16) {
      setContext({
        greeting: "Lunch O'Clock",
        subtext: "Refuel your brain for the afternoon.",
        icon: <Sun className="text-orange-500" size={28} />,
        bgGradient: "from-blue-50 to-white",
        smartTags: ["Indomie", "Juice", "Snacks", "Soda"],
      });
    } else if (hour >= 16 && hour < 22) {
      setContext({
        greeting: "Evening Groceries",
        subtext: "Time to cook. Get ingredients delivered in minutes.",
        icon: <Moon className="text-indigo-500" size={28} />,
        bgGradient: "from-indigo-50 to-purple-50",
        smartTags: ["Maize Flour", "Rice", "Cooking Oil", "Tomatoes"],
      });
    } else {
      setContext({
        greeting: "Late Night Hustle",
        subtext: "Keep the grind going.",
        icon: <Moon className="text-gray-800" size={28} />,
        bgGradient: "from-gray-100 to-gray-200",
        smartTags: ["Energy Drinks", "Coffee", "Water", "Biscuits"],
      });
    }
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Route to our discovery engine with the query
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleSmartTagClick = (tag) => {
    // Instantly search when they click a smart suggestion
    navigate(`/search?q=${encodeURIComponent(tag)}`);
  };

  if (!context) return null;

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* 1. DYNAMIC HERO SECTION */}
      <div
        className={`pt-12 pb-8 px-4 bg-gradient-to-b ${context.bgGradient} rounded-b-[40px] shadow-sm`}
      >
        <div className="flex items-center space-x-3 mb-2">
          {context.icon}
          <h1 className="text-2xl font-bold text-gray-900">
            {context.greeting}
          </h1>
        </div>
        <p className="text-gray-600 mb-6">{context.subtext}</p>

        {/* 2. THE MAIN SEARCH BAR */}
        <form
          onSubmit={handleSearch}
          className="relative shadow-lg rounded-2xl"
        >
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="text-gray-400" size={20} />
          </div>
          <input
            type="text"
            className="block w-full pl-12 pr-4 py-4 rounded-2xl border-none focus:ring-2 focus:ring-bomet-blue text-lg outline-none"
            placeholder="Search for groceries, snacks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button
            type="submit"
            className="absolute inset-y-2 right-2 bg-bomet-green text-white px-4 rounded-xl font-medium hover:bg-green-700 transition"
          >
            Find
          </button>
        </form>
      </div>

      {/* 3. SMART ONE-TAP TAGS */}
      <div className="px-4 mt-6">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Trending Right Now
        </h3>
        <div className="flex flex-wrap gap-2">
          {context.smartTags.map((tag, index) => (
            <button
              key={index}
              onClick={() => handleSmartTagClick(tag)}
              className="bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100 text-sm font-medium text-gray-700 hover:border-bomet-blue hover:text-bomet-blue transition-colors"
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Future Section: "Stores Near You" Map preview could go here */}
      <div className="px-4 mt-10">
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-50 p-2 rounded-lg">
              <Navigation className="text-bomet-blue" size={24} />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">
                Delivery to Campus
              </h4>
              <p className="text-xs text-gray-500">Using your GPS location</p>
            </div>
          </div>
          <button className="text-bomet-blue text-sm font-medium">
            Change
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomerHome;
