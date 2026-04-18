'use client';

import { useState, useEffect } from 'react';
import { trips, qr, Trip } from '@/lib/api';
import Link from 'next/link';

export default function TripsPage() {
  const [activeTrips, setActiveTrips] = useState<Trip[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [scanValue, setScanValue] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);

  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const data = await trips.list();
      setActiveTrips(data.items || []);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleTransition = async (tripId: string, newState: string) => {
    setLoading(true);
    try {
      await trips.transition(tripId, newState);
      await fetchTrips();
      if (selectedTrip?.id === tripId) {
        const updated = await trips.get(tripId);
        setSelectedTrip(updated);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTrip || !scanValue) return;

    setLoading(true);
    setScanResult(null);
    try {
      const res: any = await qr.scan(selectedTrip.id, scanValue);
      setScanResult(`Boarding successful: ${res.passenger_name || 'Passenger'}`);
      setScanValue('');
      // Refresh trip to see updated seat count
      const updated = await trips.get(selectedTrip.id);
      setSelectedTrip(updated);
      fetchTrips();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trip / Driver Console</h1>
            <p className="text-gray-600">Manage trip lifecycle and validate passenger boardings.</p>
          </div>
          <Link href="/" className="text-gray-500 hover:text-gray-900">← Back</Link>
        </header>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
            <p>{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Trip List */}
          <section className="lg:col-span-1 space-y-4">
            <h2 className="text-xl font-bold mb-4">Active Trips</h2>
            {activeTrips.map((trip) => (
              <button
                key={trip.id}
                onClick={() => setSelectedTrip(trip)}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                  selectedTrip?.id === trip.id
                    ? 'border-orange-500 bg-orange-50 ring-4 ring-orange-100'
                    : 'bg-white border-gray-100 hover:border-gray-300'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-gray-900">{trip.vehicle_id}</span>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    trip.state === 'boarding' ? 'bg-green-100 text-green-700' :
                    trip.state === 'enroute' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {trip.state}
                  </span>
                </div>
                <div className="text-sm text-gray-500 mb-2">Route: {trip.route_id}</div>
                <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                  <div 
                    className="bg-orange-500 h-full transition-all" 
                    style={{ width: `${((trip.seats_total - trip.seats_free) / trip.seats_total) * 100}%` }}
                  />
                </div>
                <div className="mt-1 text-[10px] text-gray-400 text-right uppercase font-bold">
                  {trip.seats_total - trip.seats_free} / {trip.seats_total} Seats
                </div>
              </button>
            ))}
          </section>

          {/* Trip Details & Boarding */}
          <section className="lg:col-span-2">
            {selectedTrip ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-gray-900 p-6 text-white flex justify-between items-center">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedTrip.vehicle_id}</h2>
                    <p className="text-gray-400 text-sm">Driver: {selectedTrip.driver_id}</p>
                  </div>
                  <div className="flex space-x-2">
                    {selectedTrip.state === 'planned' && (
                      <button
                        onClick={() => handleTransition(selectedTrip.id, 'boarding')}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-bold"
                      >
                        Start Boarding
                      </button>
                    )}
                    {selectedTrip.state === 'boarding' && (
                      <button
                        onClick={() => handleTransition(selectedTrip.id, 'enroute')}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-bold"
                      >
                        Depart
                      </button>
                    )}
                    {selectedTrip.state === 'enroute' && (
                      <button
                        onClick={() => handleTransition(selectedTrip.id, 'completed')}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-sm font-bold"
                      >
                        Complete Trip
                      </button>
                    )}
                  </div>
                </div>

                <div className="p-8">
                  {selectedTrip.state === 'boarding' ? (
                    <div className="space-y-8">
                      <div className="p-6 bg-orange-50 border-2 border-dashed border-orange-200 rounded-2xl">
                        <h3 className="text-lg font-bold text-orange-900 mb-4">Board Passenger</h3>
                        <form onSubmit={handleScan} className="flex space-x-3">
                          <input
                            type="text"
                            placeholder="Scan or enter QR token..."
                            value={scanValue}
                            onChange={(e) => setScanValue(e.target.value)}
                            className="flex-1 p-4 bg-white border border-orange-200 rounded-xl outline-none focus:ring-2 focus:ring-orange-500 font-mono"
                          />
                          <button
                            type="submit"
                            disabled={loading}
                            className="px-8 bg-orange-600 text-white rounded-xl font-bold hover:bg-orange-700 transition-all shadow-md"
                          >
                            Scan
                          </button>
                        </form>
                        {scanResult && (
                          <div className="mt-4 p-3 bg-green-100 border border-green-200 text-green-800 rounded-lg text-sm font-bold animate-in fade-in zoom-in-95">
                            {scanResult}
                          </div>
                        )}
                      </div>

                      <div>
                        <h3 className="font-bold text-gray-700 mb-4 uppercase text-xs tracking-widest">Boarding Progress</h3>
                        <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
                          {[...Array(selectedTrip.seats_total)].map((_, i) => {
                            const isOccupied = i < (selectedTrip.seats_total - selectedTrip.seats_free);
                            return (
                              <div
                                key={i}
                                className={`aspect-square rounded-lg flex items-center justify-center font-bold text-xs ${
                                  isOccupied ? 'bg-orange-500 text-white' : 'bg-gray-100 text-gray-400'
                                }`}
                              >
                                {i + 1}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-20 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                      <div className="text-4xl mb-4">🚦</div>
                      <h3 className="text-xl font-bold text-gray-900">
                        {selectedTrip.state === 'planned' ? 'Ready for Boarding' : 
                         selectedTrip.state === 'enroute' ? 'Trip in Progress' : 
                         'Trip Completed'}
                      </h3>
                      <p className="text-gray-500 max-w-xs mx-auto mt-2">
                        {selectedTrip.state === 'planned' ? 'Start boarding when the vehicle is at the rank and ready.' :
                         selectedTrip.state === 'enroute' ? 'Vehicle is currently on the route. Monitor telemetry updates.' :
                         'All data for this trip has been finalized.'}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center p-12 bg-white rounded-2xl border-2 border-dashed border-gray-200 text-gray-400">
                <div className="text-center">
                  <div className="text-6xl mb-4">🚌</div>
                  <p className="text-lg">Select a trip to manage its operational state.</p>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
