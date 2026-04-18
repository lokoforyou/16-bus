'use client';

import { useState, useEffect } from 'react';
import { routes, stops as stopsApi, trips as tripsApi, bookings, Route, Stop, Booking } from '@/lib/api';
import Link from 'next/link';

export default function BookingPage() {
  const [availableRoutes, setAvailableRoutes] = useState<Route[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('');
  const [stops, setStops] = useState<Stop[]>([]);
  const [originId, setOriginId] = useState<string>('');
  const [destinationId, setDestinationId] = useState<string>('');
  const [partySize, setPartySize] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);

  useEffect(() => {
    setLoading(true);
    routes.list()
      .then(res => setAvailableRoutes(res.items))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedRouteId) {
      setLoading(true);
      fetchStops();
    }
  }, [selectedRouteId]);

  const fetchStops = async () => {
    try {
      const data = await stopsApi.list();
      setStops(data.items);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBooking = async () => {
    if (!originId || !destinationId) {
      setError('Please select origin and destination.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const tripsData = await tripsApi.list();
      const targetTrip = tripsData.items?.find((trip) => trip.route_id === selectedRouteId);

      if (!targetTrip) throw new Error('No active trips found for this route.');

      const newBooking = await bookings.create(targetTrip.id, originId, destinationId, partySize);
      setBooking(newBooking);
      
      // Auto-pay for the probe
      await bookings.pay(newBooking.id, 'wallet', newBooking.fare_amount || 25.0);
      const updatedBooking = await bookings.get(newBooking.id);
      setBooking(updatedBooking);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (booking) {
    return (
      <main className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-green-600 p-6 text-white text-center">
            <div className="text-4xl mb-2">✅</div>
            <h2 className="text-2xl font-bold">Booking Confirmed!</h2>
            <p className="opacity-90">Your seat is reserved.</p>
          </div>
          <div className="p-8 space-y-6">
            <div className="flex justify-center">
              <div className="w-48 h-48 bg-gray-100 border-4 border-gray-200 rounded-lg flex items-center justify-center relative">
                {/* Mock QR Code */}
                <div className="grid grid-cols-4 gap-1 p-4">
                  {[...Array(16)].map((_, i) => (
                    <div key={i} className={`w-6 h-6 ${Math.random() > 0.5 ? 'bg-black' : 'bg-white'}`} />
                  ))}
                </div>
                <div className="absolute inset-0 flex items-center justify-center bg-white/10 backdrop-blur-[1px]">
                  <span className="bg-white px-2 py-1 text-xs font-mono font-bold border border-gray-300 shadow-sm">
                    {booking.qr_token_id || 'QR-123-ABC'}
                  </span>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Booking ID</span>
                <span className="font-mono font-medium">{booking.id.slice(0, 8)}...</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Party Size</span>
                <span className="font-medium">{booking.party_size} Passenger(s)</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Fare</span>
                <span className="font-medium text-green-600">R {booking.fare_amount || 25}.00 (Paid)</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">State</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-bold uppercase">
                  {booking.booking_state}
                </span>
              </div>
            </div>
            <button
              onClick={() => setBooking(null)}
              className="w-full py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-black transition-colors"
            >
              Book Another Trip
            </button>
            <Link
              href="/"
              className="block w-full text-center py-3 text-gray-500 hover:text-gray-700 transition-colors"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Passenger Booking</h1>
            <p className="text-gray-600">Secure your seat on the next available trip.</p>
          </div>
          <Link href="/" className="text-gray-500 hover:text-gray-900">← Back</Link>
        </header>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-8 space-y-8">
            {/* Step 1: Select Route */}
            <section>
              <label className="block text-sm font-bold text-gray-700 mb-3 uppercase tracking-wider">
                1. Select Route
              </label>
              <div className="grid grid-cols-1 gap-3">
                {availableRoutes.map((route) => (
                  <button
                    key={route.id}
                    onClick={() => setSelectedRouteId(route.id)}
                    className={`p-4 text-left rounded-xl border-2 transition-all ${
                      selectedRouteId === route.id
                        ? 'border-blue-600 bg-blue-50 ring-4 ring-blue-100'
                        : 'border-gray-100 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-bold text-gray-900">{route.name}</div>
                    <div className="text-sm text-gray-500 font-mono uppercase">{route.code} • {route.direction}</div>
                  </button>
                ))}
              </div>
            </section>

            {/* Step 2: Stops & Party Size */}
            {selectedRouteId && (
              <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <label className="block text-sm font-bold text-gray-700 mb-3 uppercase tracking-wider">
                  2. Trip Details
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm text-gray-500 mb-1">Origin Stop</label>
                    <select
                      value={originId}
                      onChange={(e) => setOriginId(e.target.value)}
                      className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">Select Pickup</option>
                      {stops.map(stop => (
                        <option key={stop.id} value={stop.id}>{stop.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-500 mb-1">Destination Stop</label>
                    <select
                      value={destinationId}
                      onChange={(e) => setDestinationId(e.target.value)}
                      className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">Select Drop-off</option>
                      {stops.map(stop => (
                        <option key={stop.id} value={stop.id}>{stop.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-6">
                  <label className="block text-sm text-gray-500 mb-1">Number of Passengers</label>
                  <div className="flex items-center space-x-4">
                    {[1, 2, 3, 4].map(num => (
                      <button
                        key={num}
                        onClick={() => setPartySize(num)}
                        className={`w-12 h-12 rounded-lg border-2 font-bold transition-all ${
                          partySize === num
                            ? 'border-blue-600 bg-blue-600 text-white'
                            : 'border-gray-200 text-gray-600 hover:border-gray-400'
                        }`}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* Step 3: Confirmation */}
            {originId && destinationId && (
              <section className="pt-8 border-t border-gray-100 animate-in fade-in zoom-in-95 duration-300">
                <div className="bg-gray-900 rounded-2xl p-6 text-white shadow-lg">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h3 className="text-xl font-bold">Booking Summary</h3>
                      <p className="text-gray-400 text-sm">Next available trip</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-400">R {partySize * 25}.00</div>
                      <div className="text-xs text-gray-400 uppercase tracking-widest">Est. Fare</div>
                    </div>
                  </div>
                  <button
                    onClick={handleBooking}
                    disabled={loading}
                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-xl font-bold text-lg transition-all shadow-lg active:scale-[0.98]"
                  >
                    {loading ? 'Processing...' : 'Reserve Seat & Pay'}
                  </button>
                  <p className="mt-4 text-center text-xs text-gray-500">
                    By clicking you agree to the 16 Bus transport terms and SLA.
                  </p>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
