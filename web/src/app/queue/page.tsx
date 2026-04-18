'use client';

import { useState, useEffect } from 'react';
import { rank, trips, Route, Stop, Trip } from '@/lib/api';
import Link from 'next/link';

interface QueueTicket {
  id: string;
  rank_id: string;
  trip_id?: string;
  queue_number: number;
  state: string;
  qr_token_id?: string;
}

export default function QueuePage() {
  const [activeTickets, setActiveTickets] = useState<QueueTicket[]>([]);
  const [activeTrips, setActiveTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reconciliation, setReconciliation] = useState<any>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [reconRes, tripsData] = await Promise.all([fetch('http://localhost:8000/api/v1/rank/reconciliation/current'), trips.list()]);
      const reconData = await reconRes.json();
      setReconciliation(reconData);
      setActiveTrips(tripsData.items || []);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleIssueTicket = async () => {
    setLoading(true);
    setError(null);
    try {
      await rank.issueTicket('stop-bara-rank');
      await fetchData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Rank Queue Management</h1>
            <p className="text-gray-600">Digitize the walk-up queue and manage boarding order.</p>
          </div>
          <Link href="/" className="text-gray-500 hover:text-gray-900">← Back</Link>
        </header>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
            <p>{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <span className="block text-sm text-gray-500 uppercase font-bold tracking-wider mb-1">Total Issued</span>
            <span className="text-3xl font-bold text-gray-900">{reconciliation?.tickets_total || 0}</span>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <span className="block text-sm text-gray-500 uppercase font-bold tracking-wider mb-1">Assigned</span>
            <span className="text-3xl font-bold text-blue-600">{reconciliation?.tickets_assigned || 0}</span>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <span className="block text-sm text-gray-500 uppercase font-bold tracking-wider mb-1">Boarded</span>
            <span className="text-3xl font-bold text-green-600">{reconciliation?.tickets_boarded || 0}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Action Panel */}
          <section className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <h2 className="text-xl font-bold mb-4">Marshal Actions</h2>
              <button
                onClick={handleIssueTicket}
                disabled={loading}
                className="w-full py-6 bg-green-600 hover:bg-green-700 text-white rounded-2xl font-bold text-xl shadow-lg transition-all active:scale-[0.98] flex flex-col items-center"
              >
                <span>Issue Queue Ticket</span>
                <span className="text-xs font-normal opacity-80 mt-1">Generate QR for walk-up passenger</span>
              </button>
              
              <div className="mt-8 pt-8 border-t border-gray-100">
                <h3 className="font-bold mb-4">Current Trips at Rank</h3>
                <div className="space-y-3">
                  {activeTrips.filter(t => t.state === 'boarding').map(trip => (
                    <div key={trip.id} className="p-4 bg-gray-50 rounded-xl border border-gray-200 flex justify-between items-center">
                      <div>
                        <div className="font-bold">{trip.vehicle_id}</div>
                        <div className="text-xs text-gray-500">{trip.seats_free} seats available</div>
                      </div>
                      <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-bold hover:bg-blue-200">
                        Assign Next in Queue
                      </button>
                    </div>
                  ))}
                  {activeTrips.filter(t => t.state === 'boarding').length === 0 && (
                    <p className="text-center text-gray-400 py-4 italic">No vehicles currently boarding.</p>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* Queue Visualization */}
          <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <h2 className="text-xl font-bold mb-6">Live Queue State</h2>
            <div className="space-y-4">
              {/* This is a visual representation of the queue logic */}
              <div className="relative pl-8 border-l-2 border-dashed border-gray-200 space-y-8">
                <div className="relative">
                  <div className="absolute -left-[41px] top-0 w-4 h-4 rounded-full bg-blue-600 ring-4 ring-blue-100" />
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                    <div className="flex justify-between">
                      <span className="font-bold text-blue-900">Next to Board</span>
                      <span className="text-xs font-mono bg-blue-200 px-2 py-0.5 rounded text-blue-800">#042</span>
                    </div>
                    <p className="text-sm text-blue-700 mt-1">Waiting for assignment...</p>
                  </div>
                </div>
                
                <div className="relative">
                  <div className="absolute -left-[41px] top-0 w-4 h-4 rounded-full bg-gray-300" />
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-900">In Line</span>
                      <span className="text-xs font-mono bg-gray-200 px-2 py-0.5 rounded text-gray-600">#043</span>
                    </div>
                  </div>
                </div>

                <div className="relative opacity-50">
                  <div className="absolute -left-[41px] top-0 w-4 h-4 rounded-full bg-gray-200" />
                  <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-400">Recently Boarded</span>
                      <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-400">#041</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-12 p-4 bg-orange-50 rounded-xl border border-orange-100">
              <h3 className="text-sm font-bold text-orange-800 mb-2 uppercase flex items-center">
                <span className="mr-2">💡</span>
                Marshal Insight
              </h3>
              <p className="text-sm text-orange-700">
                Boarding is currently at 62% capacity for the Soweto route. Consider opening an additional trip for the 17:30 peak.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
