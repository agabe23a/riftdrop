import { useState, useEffect, useRef } from "react";
import {
  MapPin,
  Navigation,
  CheckCircle,
  AlertTriangle,
  KeyRound,
} from "lucide-react";
import apiClient from "../api/client";

const RiderRadar = () => {
  const [connectionStatus, setConnectionStatus] = useState(
    "Connecting to Radar...",
  );
  const [availableJobs, setAvailableJobs] = useState([]);
  const [activeJob, setActiveJob] = useState(null); // The job the rider is currently doing
  const [pinInput, setPinInput] = useState("");
  const [error, setError] = useState("");
  const ws = useRef(null);

  // In production, grab the rider's ID from the JWT token memory
  const token = localStorage.getItem("riftdrop_token");

  // --- 1. THE WEBSOCKET RADAR ---
  useEffect(() => {
    if (!token) {
      setConnectionStatus("Authentication Error");
      return;
    }

    const wsUrl = `ws://127.0.0.1:8000/api/v1/logistics/ws/rider?token=${token}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () =>
      setConnectionStatus("Radar Online: Searching for jobs...");

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "NEW_DELIVERY_AVAILABLE") {
        // A new order was paid for! Add it to the radar.
        setAvailableJobs((prev) => [
          {
            order_id: data.order_id,
            payout: data.payout || 50.0,
            distance: "1.2 km", // In production, calculated via Haversine
            pickup: "K-Matt Supermarket",
            dropoff: "Bomet Hostels",
          },
          ...prev,
        ]);
      }
    };

    ws.current.onclose = () =>
      setConnectionStatus("Radar Offline. Reconnecting...");

    return () => ws.current && ws.current.close();
  }, [token]);

  // --- 2. CLAIMING THE JOB ---
  const handleClaimJob = async (job) => {
    try {
      await apiClient.post(`/logistics/claim-order/${job.order_id}`);

      // Move from "Available" to "Active"
      setActiveJob(job);
      setAvailableJobs((prev) =>
        prev.filter((j) => j.order_id !== job.order_id),
      );
    } catch (err) {
      setError(
        err.response?.data?.detail || "Someone else claimed this order first!",
      );
    }
  };

  // --- 3. ZERO-TRUST PIN VERIFICATION ---
  const handleCompleteDelivery = async () => {
    setError("");
    if (pinInput.length !== 4) {
      setError("PIN must be exactly 4 digits.");
      return;
    }

    try {
      await apiClient.post(`/logistics/complete-delivery/${activeJob.order_id}`, { pin: pinInput });
      setActiveJob(null);
      setPinInput("");
    } catch (error) {
      setError(error.response?.data?.detail || "Delivery not completed.");
    }
  };

  return (
    <div className="min-h-screen bg-[#111827] text-white font-sans flex flex-col">
      {/* RIDER HEADER */}
      <div className="bg-[#1F2937] px-6 py-5 shadow-md flex justify-between items-center border-b border-gray-800">
        <div>
          <h1 className="text-xl font-black text-bomet-gold tracking-widest uppercase">
            Rider Ops
          </h1>
          <p className="text-xs text-gray-400 mt-1 flex items-center">
            <span
              className={`w-2 h-2 rounded-full mr-2 ${connectionStatus.includes("Online") ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
            ></span>
            {connectionStatus}
          </p>
        </div>
        <div className="bg-gray-800 p-3 rounded-full">
          <Navigation size={24} className="text-blue-400" />
        </div>
      </div>

      <div className="flex-1 p-4">
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-xl mb-4 text-sm flex items-start">
            <AlertTriangle size={18} className="mr-2 mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        {/* STATE A: ACTIVE DELIVERY (Rider has a package) */}
        {activeJob ? (
          <div className="bg-[#1F2937] rounded-2xl p-6 border border-bomet-gold shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-bomet-gold text-gray-900 text-xs font-bold px-3 py-1 rounded-bl-lg">
              ACTIVE MISSION
            </div>

            <h2 className="text-2xl font-black mb-4">
              Order #{activeJob.order_id}
            </h2>

            <div className="space-y-4 mb-8">
              <div className="flex items-start">
                <div className="bg-gray-800 p-2 rounded-full mr-3">
                  <MapPin size={18} className="text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">
                    Pickup
                  </p>
                  <p className="font-medium text-lg">{activeJob.pickup}</p>
                </div>
              </div>
              <div className="border-l-2 border-dashed border-gray-700 ml-4 h-6"></div>
              <div className="flex items-start">
                <div className="bg-gray-800 p-2 rounded-full mr-3">
                  <CheckCircle size={18} className="text-green-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">
                    Dropoff
                  </p>
                  <p className="font-medium text-lg">{activeJob.dropoff}</p>
                </div>
              </div>
            </div>

            <div className="bg-black/30 p-5 rounded-xl border border-gray-700">
              <p className="text-sm text-gray-400 text-center mb-3">
                Ask customer for the 4-digit Delivery PIN to release your
                payout.
              </p>
              <div className="flex items-center bg-gray-900 rounded-lg p-2 border border-gray-600 mb-4 focus-within:border-bomet-gold transition-colors">
                <KeyRound size={20} className="text-gray-500 ml-2" />
                <input
                  type="text"
                  maxLength="4"
                  placeholder="Enter PIN"
                  value={pinInput}
                  onChange={(e) =>
                    setPinInput(e.target.value.replace(/\D/g, ""))
                  }
                  className="bg-transparent w-full text-center text-3xl tracking-[0.5em] font-black text-white outline-none"
                />
              </div>
              <button
                onClick={handleCompleteDelivery}
                className="w-full bg-bomet-green hover:bg-green-600 text-white font-bold py-4 rounded-xl transition shadow-lg flex justify-center items-center"
              >
                Complete & Release KES {activeJob.payout}
              </button>
            </div>
          </div>
        ) : (
          /* STATE B: IDLE (Looking for jobs) */
          <div className="space-y-4">
            {availableJobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <div className="w-24 h-24 rounded-full border-4 border-gray-800 border-t-blue-500 animate-spin mb-4"></div>
                <p className="text-gray-400">Scanning for nearby orders...</p>
              </div>
            ) : (
              availableJobs.map((job) => (
                <div
                  key={job.order_id}
                  className="bg-[#1F2937] rounded-xl p-5 border border-gray-700 shadow-lg"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <span className="bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded font-medium">
                        Order #{job.order_id}
                      </span>
                      <p className="text-sm text-gray-400 mt-2">
                        <MapPin size={14} className="inline mr-1" />{" "}
                        {job.distance} away
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-400 uppercase">Payout</p>
                      <p className="text-2xl font-black text-green-400">
                        KES {job.payout}
                      </p>
                    </div>
                  </div>

                  <div className="flex space-x-2 text-sm text-gray-300 mb-4 bg-black/20 p-3 rounded-lg">
                    <span className="truncate flex-1">{job.pickup}</span>
                    <span className="text-gray-600">→</span>
                    <span className="truncate flex-1 text-right">
                      {job.dropoff}
                    </span>
                  </div>

                  <button
                    onClick={() => handleClaimJob(job)}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition shadow-lg"
                  >
                    Tap to Claim Mission
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RiderRadar;
