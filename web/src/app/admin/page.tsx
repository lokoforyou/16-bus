'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { useAuth } from '@/components/app-shell';
import {
  ApiError,
  bookings,
  drivers,
  organizations,
  routes,
  stops,
  trips,
  users,
  vehicles,
  type Booking,
  type Driver,
  type Route,
  type Stop,
  type Trip,
  type User,
} from '@/lib/api';

type OrgForm = { name: string; type: string; compliance_status: string; is_active: boolean };
type StopForm = { id: string; name: string; type: string; lat: number; lon: number; cash_allowed: boolean; active: boolean };
type UserForm = { full_name: string; phone: string; password: string; role: 'super_admin' | 'org_admin' | 'driver' | 'marshal' | 'passenger'; organization_id: string; is_active: boolean };
type DriverForm = { organization_id: string; user_id: string; full_name: string; phone: string; licence_number: string; pdp_verified: boolean; is_active: boolean };
type TripForm = {
  id: string; route_id: string; route_variant_id: string; organization_id: string; vehicle_id: string; driver_id: string;
  trip_type: string; planned_start_time: string; state: string; seats_total: number; seats_free: number; current_stop_id: string;
};
type BookingForm = { passenger_id: string; route_id: string; origin_stop_id: string; destination_stop_id: string; party_size: number; booking_channel: string };
type VehicleRow = { id: string; organization_id: string; plate_number: string; capacity: number; permit_number?: string | null; compliance_status: string; is_active: boolean };
type VehicleForm = { organization_id: string; plate_number: string; capacity: number; permit_number: string; compliance_status: string; is_active: boolean };

const orgBlank: OrgForm = { name: '', type: 'taxi_association', compliance_status: 'pending', is_active: true };
const stopBlank: StopForm = { id: '', name: '', type: 'rank', lat: 0, lon: 0, cash_allowed: false, active: true };
const userBlank: UserForm = { full_name: '', phone: '', password: '', role: 'passenger', organization_id: '', is_active: true };
const driverBlank: DriverForm = { organization_id: '', user_id: '', full_name: '', phone: '', licence_number: '', pdp_verified: false, is_active: true };
const tripBlank: TripForm = { id: '', route_id: '', route_variant_id: '', organization_id: '', vehicle_id: '', driver_id: '', trip_type: 'scheduled', planned_start_time: '', state: 'planned', seats_total: 16, seats_free: 16, current_stop_id: '' };
const bookingBlank: BookingForm = { passenger_id: '', route_id: '', origin_stop_id: '', destination_stop_id: '', party_size: 1, booking_channel: 'app' };
const vehicleBlank: VehicleForm = { organization_id: '', plate_number: '', capacity: 16, permit_number: '', compliance_status: 'pending', is_active: true };

export default function AdminPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'super_admin';

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [orgs, setOrgs] = useState<{ id: string; name: string; type: string; compliance_status: string; is_active: boolean }[]>([]);
  const [stopsList, setStopsList] = useState<Stop[]>([]);
  const [routesList, setRoutesList] = useState<Route[]>([]);
  const [usersList, setUsersList] = useState<User[]>([]);
  const [driversList, setDriversList] = useState<Driver[]>([]);
  const [tripsList, setTripsList] = useState<Trip[]>([]);
  const [bookingsList, setBookingsList] = useState<Booking[]>([]);
  const [vehicleRows, setVehicleRows] = useState<VehicleRow[]>([]);

  const [orgForm, setOrgForm] = useState<OrgForm>(orgBlank);
  const [stopForm, setStopForm] = useState<StopForm>(stopBlank);
  const [userForm, setUserForm] = useState<UserForm>(userBlank);
  const [driverForm, setDriverForm] = useState<DriverForm>(driverBlank);
  const [tripForm, setTripForm] = useState<TripForm>(tripBlank);
  const [bookingForm, setBookingForm] = useState<BookingForm>(bookingBlank);
  const [vehicleForm, setVehicleForm] = useState<VehicleForm>(vehicleBlank);

  const [orgId, setOrgId] = useState<string | null>(null);
  const [stopId, setStopId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [driverId, setDriverId] = useState<string | null>(null);
  const [tripId, setTripId] = useState<string | null>(null);
  const [vehicleId, setVehicleId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [orgRes, stopRes, routeRes, userRes, driverRes, tripRes, bookingRes, vehicleRes] = await Promise.all([
        organizations.list(),
        stops.list(),
        routes.list(),
        users.list(),
        drivers.list(),
        trips.adminList(),
        bookings.adminList(),
        vehicles.list(),
      ]);
      setOrgs(orgRes.items);
      setStopsList(stopRes.items);
      setRoutesList(routeRes.items);
      setUsersList(userRes.items);
      setDriversList(driverRes.items);
      setTripsList(tripRes);
      setBookingsList(bookingRes.items);
      setVehicleRows(vehicleRes.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  if (!isSuperAdmin) {
    return (
      <main className="mx-auto flex min-h-[60vh] max-w-3xl items-center justify-center px-6">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-10 text-center shadow-sm">
          <h1 className="text-3xl font-semibold text-slate-950">Admin access only</h1>
          <p className="mt-3 text-slate-600">This panel is restricted to super admin accounts.</p>
        </div>
      </main>
    );
  }

  const saveOrg = async () => {
    try {
      orgId ? await organizations.update(orgId, orgForm) : await organizations.create(orgForm);
      setOrgForm(orgBlank); setOrgId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save organization'); }
  };

  const saveStop = async () => {
    try {
      stopId ? await stops.update(stopId, stopForm) : await stops.create(stopForm);
      setStopForm(stopBlank); setStopId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save stop'); }
  };

  const saveUser = async () => {
    try {
      const payload = { ...userForm, organization_id: userForm.organization_id || null };
      userId ? await users.update(userId, payload) : await users.create(payload);
      setUserForm(userBlank); setUserId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save user'); }
  };

  const saveDriver = async () => {
    try {
      driverId ? await drivers.update(driverId, driverForm) : await drivers.create(driverForm);
      setDriverForm(driverBlank); setDriverId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save driver'); }
  };

  const saveTrip = async () => {
    try {
      const payload = { ...tripForm, seats_total: Number(tripForm.seats_total), seats_free: Number(tripForm.seats_free) };
      tripId ? await trips.update(tripId, payload) : await trips.create(payload);
      setTripForm(tripBlank); setTripId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save trip'); }
  };

  const saveBooking = async () => {
    try {
      await bookings.adminCreate({
        passenger_id: bookingForm.passenger_id,
        route_id: bookingForm.route_id,
        origin_stop_id: bookingForm.origin_stop_id,
        destination_stop_id: bookingForm.destination_stop_id,
        party_size: Number(bookingForm.party_size),
        booking_channel: bookingForm.booking_channel,
      });
      setBookingForm(bookingBlank); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save booking'); }
  };

  const saveVehicle = async () => {
    try {
      const payload = { ...vehicleForm, permit_number: vehicleForm.permit_number || null };
      vehicleId ? await vehicles.update(vehicleId, payload) : await vehicles.create(payload);
      setVehicleForm(vehicleBlank); setVehicleId(null); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save vehicle'); }
  };

  return (
    <main className="mx-auto max-w-7xl px-6 py-10 text-slate-900">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Super admin</p>
          <h1 className="mt-2 text-3xl font-semibold">Full operations panel</h1>
          <p className="mt-2 text-sm text-slate-600">Users, drivers, trips, bookings, organizations, stops, and routes.</p>
        </div>
        <button className="rounded-full border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50" onClick={() => void load()}>Refresh</button>
      </div>
      {error && <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700">{error}</div>}
      {loading && <div className="mb-6 text-sm text-slate-500">Loading...</div>}

      <div className="grid gap-8 lg:grid-cols-2">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Users</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Full name" value={userForm.full_name} onChange={(e) => setUserForm((c) => ({ ...c, full_name: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Phone" value={userForm.phone} onChange={(e) => setUserForm((c) => ({ ...c, phone: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Password" type="password" value={userForm.password} onChange={(e) => setUserForm((c) => ({ ...c, password: e.target.value }))} />
            <select className="rounded-2xl border px-4 py-3" value={userForm.role} onChange={(e) => setUserForm((c) => ({ ...c, role: e.target.value as UserForm['role'] }))}>
              <option value="passenger">Passenger</option><option value="driver">Driver</option><option value="marshal">Marshal</option><option value="org_admin">Org admin</option><option value="super_admin">Super admin</option>
            </select>
            <input className="rounded-2xl border px-4 py-3 md:col-span-2" placeholder="Organization ID" value={userForm.organization_id} onChange={(e) => setUserForm((c) => ({ ...c, organization_id: e.target.value }))} />
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveUser()}>{userId ? 'Update user' : 'Create user'}</button>
          <div className="mt-4 space-y-3">
            {usersList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.full_name}</div><div className="text-sm text-slate-600">{item.phone}</div><div className="text-xs uppercase tracking-[0.25em] text-slate-500">{item.role}</div></div><div className="flex gap-2"><button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setUserId(item.id); setUserForm({ full_name: item.full_name, phone: item.phone, password: '', role: item.role, organization_id: item.organization_id || '', is_active: item.is_active }); }}>Edit</button><button className="rounded-full border border-rose-200 px-3 py-1 text-sm text-rose-700" onClick={async () => { await users.remove(item.id); await load(); }}>Delete</button></div></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Drivers</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Organization ID" value={driverForm.organization_id} onChange={(e) => setDriverForm((c) => ({ ...c, organization_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="User ID" value={driverForm.user_id} onChange={(e) => setDriverForm((c) => ({ ...c, user_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Full name" value={driverForm.full_name} onChange={(e) => setDriverForm((c) => ({ ...c, full_name: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Phone" value={driverForm.phone} onChange={(e) => setDriverForm((c) => ({ ...c, phone: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Licence number" value={driverForm.licence_number} onChange={(e) => setDriverForm((c) => ({ ...c, licence_number: e.target.value }))} />
            <label className="flex items-center gap-3 rounded-2xl border px-4 py-3"><input type="checkbox" checked={driverForm.pdp_verified} onChange={(e) => setDriverForm((c) => ({ ...c, pdp_verified: e.target.checked }))} /> PDP verified</label>
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveDriver()}>{driverId ? 'Update driver' : 'Create driver'}</button>
          <div className="mt-4 space-y-3">
            {driversList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.full_name}</div><div className="text-sm text-slate-600">{item.phone}</div><div className="text-xs uppercase tracking-[0.25em] text-slate-500">{item.licence_number}</div></div><div className="flex gap-2"><button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setDriverId(item.id); setDriverForm({ organization_id: item.organization_id, user_id: item.user_id, full_name: item.full_name, phone: item.phone, licence_number: item.licence_number, pdp_verified: item.pdp_verified, is_active: item.is_active }); }}>Edit</button><button className="rounded-full border border-rose-200 px-3 py-1 text-sm text-rose-700" onClick={async () => { await drivers.remove(item.id); await load(); }}>Delete</button></div></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Trips</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Trip ID" value={tripForm.id} onChange={(e) => setTripForm((c) => ({ ...c, id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Route ID" value={tripForm.route_id} onChange={(e) => setTripForm((c) => ({ ...c, route_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Route variant ID" value={tripForm.route_variant_id} onChange={(e) => setTripForm((c) => ({ ...c, route_variant_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Organization ID" value={tripForm.organization_id} onChange={(e) => setTripForm((c) => ({ ...c, organization_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Vehicle ID" value={tripForm.vehicle_id} onChange={(e) => setTripForm((c) => ({ ...c, vehicle_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Driver ID" value={tripForm.driver_id} onChange={(e) => setTripForm((c) => ({ ...c, driver_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Trip type" value={tripForm.trip_type} onChange={(e) => setTripForm((c) => ({ ...c, trip_type: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Planned start time" value={tripForm.planned_start_time} onChange={(e) => setTripForm((c) => ({ ...c, planned_start_time: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Current stop ID" value={tripForm.current_stop_id} onChange={(e) => setTripForm((c) => ({ ...c, current_stop_id: e.target.value }))} />
            <select className="rounded-2xl border px-4 py-3" value={tripForm.state} onChange={(e) => setTripForm((c) => ({ ...c, state: e.target.value }))}>
              <option value="planned">Planned</option><option value="boarding">Boarding</option><option value="enroute">Enroute</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option>
            </select>
            <input type="number" className="rounded-2xl border px-4 py-3" placeholder="Seats total" value={tripForm.seats_total} onChange={(e) => setTripForm((c) => ({ ...c, seats_total: Number(e.target.value) }))} />
            <input type="number" className="rounded-2xl border px-4 py-3" placeholder="Seats free" value={tripForm.seats_free} onChange={(e) => setTripForm((c) => ({ ...c, seats_free: Number(e.target.value) }))} />
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveTrip()}>{tripId ? 'Update trip' : 'Create trip'}</button>
          <div className="mt-4 space-y-3">
            {tripsList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.id}</div><div className="text-sm text-slate-600">{item.route_id} · {item.vehicle_id}</div><div className="text-xs uppercase tracking-[0.25em] text-slate-500">{item.state}</div></div><div className="flex flex-wrap gap-2"><button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setTripId(item.id); setTripForm({ id: item.id, route_id: item.route_id, route_variant_id: item.route_variant_id, organization_id: item.organization_id, vehicle_id: item.vehicle_id, driver_id: item.driver_id, trip_type: item.trip_type, planned_start_time: item.planned_start_time, state: item.state, seats_total: item.seats_total, seats_free: item.seats_free, current_stop_id: item.current_stop_id }); }}>Edit</button><button className="rounded-full border px-3 py-1 text-sm" onClick={async () => { await trips.transition(item.id, 'boarding'); await load(); }}>Board</button><button className="rounded-full border px-3 py-1 text-sm" onClick={async () => { await trips.transition(item.id, 'enroute'); await load(); }}>Depart</button><button className="rounded-full border px-3 py-1 text-sm" onClick={async () => { await trips.transition(item.id, 'cancelled'); await load(); }}>Cancel</button></div></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Vehicles</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Organization ID" value={vehicleForm.organization_id} onChange={(e) => setVehicleForm((c) => ({ ...c, organization_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Plate number" value={vehicleForm.plate_number} onChange={(e) => setVehicleForm((c) => ({ ...c, plate_number: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Capacity" type="number" value={vehicleForm.capacity} onChange={(e) => setVehicleForm((c) => ({ ...c, capacity: Number(e.target.value) }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Permit number" value={vehicleForm.permit_number} onChange={(e) => setVehicleForm((c) => ({ ...c, permit_number: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Compliance status" value={vehicleForm.compliance_status} onChange={(e) => setVehicleForm((c) => ({ ...c, compliance_status: e.target.value }))} />
            <label className="flex items-center gap-3 rounded-2xl border px-4 py-3"><input type="checkbox" checked={vehicleForm.is_active} onChange={(e) => setVehicleForm((c) => ({ ...c, is_active: e.target.checked }))} /> Active</label>
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveVehicle()}>{vehicleId ? 'Update vehicle' : 'Create vehicle'}</button>
          <div className="mt-4 space-y-3">
            {vehicleRows.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold">{item.plate_number}</div>
                    <div className="text-sm text-slate-600">{item.organization_id} · {item.capacity} seats</div>
                  </div>
                  <button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setVehicleId(item.id); setVehicleForm({ organization_id: item.organization_id, plate_number: item.plate_number, capacity: item.capacity, permit_number: item.permit_number || '', compliance_status: item.compliance_status, is_active: item.is_active }); }}>Edit</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Bookings</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Passenger ID" value={bookingForm.passenger_id} onChange={(e) => setBookingForm((c) => ({ ...c, passenger_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Route ID" value={bookingForm.route_id} onChange={(e) => setBookingForm((c) => ({ ...c, route_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Origin stop ID" value={bookingForm.origin_stop_id} onChange={(e) => setBookingForm((c) => ({ ...c, origin_stop_id: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Destination stop ID" value={bookingForm.destination_stop_id} onChange={(e) => setBookingForm((c) => ({ ...c, destination_stop_id: e.target.value }))} />
            <input type="number" className="rounded-2xl border px-4 py-3" placeholder="Party size" value={bookingForm.party_size} onChange={(e) => setBookingForm((c) => ({ ...c, party_size: Number(e.target.value) }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Channel" value={bookingForm.booking_channel} onChange={(e) => setBookingForm((c) => ({ ...c, booking_channel: e.target.value }))} />
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveBooking()}>Create booking</button>
          <div className="mt-4 space-y-3">
            {bookingsList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.id}</div><div className="text-sm text-slate-600">{item.trip_id} · {item.passenger_id}</div><div className="text-xs uppercase tracking-[0.25em] text-slate-500">{item.booking_state} / {item.payment_status}</div></div><button className="rounded-full border border-rose-200 px-3 py-1 text-sm text-rose-700" onClick={async () => { await bookings.adminCancel(item.id); await load(); }}>Cancel</button></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Organizations</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="Name" value={orgForm.name} onChange={(e) => setOrgForm((c) => ({ ...c, name: e.target.value }))} />
            <select className="rounded-2xl border px-4 py-3" value={orgForm.type} onChange={(e) => setOrgForm((c) => ({ ...c, type: e.target.value }))}>
              <option value="taxi_association">Taxi association</option><option value="private_operator">Private operator</option><option value="government">Government</option>
            </select>
            <input className="rounded-2xl border px-4 py-3" placeholder="Compliance status" value={orgForm.compliance_status} onChange={(e) => setOrgForm((c) => ({ ...c, compliance_status: e.target.value }))} />
            <label className="flex items-center gap-3 rounded-2xl border px-4 py-3"><input type="checkbox" checked={orgForm.is_active} onChange={(e) => setOrgForm((c) => ({ ...c, is_active: e.target.checked }))} /> Active</label>
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveOrg()}>{orgId ? 'Update organization' : 'Create organization'}</button>
          <div className="mt-4 space-y-3">
            {orgs.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.name}</div><div className="text-sm text-slate-600">{item.type}</div></div><div className="flex gap-2"><button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setOrgId(item.id); setOrgForm({ name: item.name, type: item.type, compliance_status: item.compliance_status, is_active: item.is_active }); }}>Edit</button><button className="rounded-full border border-rose-200 px-3 py-1 text-sm text-rose-700" onClick={async () => { await organizations.remove(item.id); await load(); }}>Delete</button></div></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Stops</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-2xl border px-4 py-3" placeholder="ID" value={stopForm.id} onChange={(e) => setStopForm((c) => ({ ...c, id: e.target.value }))} disabled={Boolean(stopId)} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Name" value={stopForm.name} onChange={(e) => setStopForm((c) => ({ ...c, name: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Type" value={stopForm.type} onChange={(e) => setStopForm((c) => ({ ...c, type: e.target.value }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Lat" type="number" value={stopForm.lat} onChange={(e) => setStopForm((c) => ({ ...c, lat: Number(e.target.value) }))} />
            <input className="rounded-2xl border px-4 py-3" placeholder="Lon" type="number" value={stopForm.lon} onChange={(e) => setStopForm((c) => ({ ...c, lon: Number(e.target.value) }))} />
            <label className="flex items-center gap-3 rounded-2xl border px-4 py-3"><input type="checkbox" checked={stopForm.cash_allowed} onChange={(e) => setStopForm((c) => ({ ...c, cash_allowed: e.target.checked }))} /> Cash allowed</label>
          </div>
          <button className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white" onClick={() => void saveStop()}>{stopId ? 'Update stop' : 'Create stop'}</button>
          <div className="mt-4 space-y-3">
            {stopsList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-4"><div><div className="font-semibold">{item.name}</div><div className="text-sm text-slate-600">{item.type}</div></div><div className="flex gap-2"><button className="rounded-full border px-3 py-1 text-sm" onClick={() => { setStopId(item.id); setStopForm({ id: item.id, name: item.name, type: item.type, lat: item.lat, lon: item.lon, cash_allowed: item.cash_allowed, active: item.active }); }}>Edit</button><button className="rounded-full border border-rose-200 px-3 py-1 text-sm text-rose-700" onClick={async () => { await stops.remove(item.id); await load(); }}>Delete</button></div></div></div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Routes</h2>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            Route create/edit remains in the existing routes workflow. This panel focuses on the core operational CRUD above.
          </div>
          <div className="mt-4 space-y-3">
            {routesList.map((item) => (
              <div key={item.id} className="rounded-2xl border p-4">
                <div className="font-semibold">{item.code}</div>
                <div className="text-sm text-slate-600">{item.name} · {item.direction}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
