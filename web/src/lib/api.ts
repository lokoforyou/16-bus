/**
 * 16 Bus API Client
 * Centralized layer for all backend communications.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// --- Types ---

export type UserRole = 'super_admin' | 'org_admin' | 'driver' | 'marshal' | 'passenger';

export interface User {
  id: string;
  full_name: string;
  phone: string;
  role: UserRole;
  organization_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface Route {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  direction: string;
  active: boolean;
}

export interface Stop {
  id: string;
  name: string;
  type: string;
  lat: number;
  lon: number;
  cash_allowed: boolean;
  active: boolean;
}

export interface RouteStop {
  id: string;
  route_variant_id: string;
  stop_id: string;
  sequence_number: number;
  dwell_time_seconds: number;
}

export interface Trip {
  id: string;
  route_id: string;
  route_variant_id: string;
  organization_id: string;
  vehicle_id: string;
  driver_id: string;
  state: string;
  seats_total: number;
  seats_free: number;
  planned_start_time: string;
  actual_start_time?: string;
  current_stop_id: string;
  trip_type: string;
}

export interface Booking {
  id: string;
  trip_id: string;
  passenger_id: string;
  origin_stop_id: string;
  destination_stop_id: string;
  party_size: number;
  fare_amount: number;
  payment_status: string;
  booking_state: string;
  qr_token_id?: string;
}

export interface Driver {
  id: string;
  organization_id: string;
  user_id: string;
  full_name: string;
  phone: string;
  licence_number: string;
  pdp_verified: boolean;
  is_active: boolean;
  created_at: string;
}

// --- Fetcher Helper ---

async function fetcher<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = typeof errorData?.detail === 'string' ? errorData.detail : `HTTP error ${response.status}`;
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function authedFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  return fetcher<T>(path, options);
}

// --- Auth API ---

export const auth = {
  login: async (phone: string, password: string): Promise<AuthToken> => {
    const data = await fetcher<AuthToken>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    });
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', data.access_token);
    }
    return data;
  },
  register: (data: {
    full_name: string;
    phone: string;
    password: string;
    role: UserRole;
    organization_id?: string | null;
    is_active?: boolean;
  }) =>
    fetcher<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  },
  me: () => fetcher<User>('/auth/me'),
};

// --- Routes & Stops API ---

export const routes = {
  list: () => fetcher<{ items: Route[] }>('/routes'),
  listStops: (routeId: string) => fetcher<{ items: RouteStop[] }>(`/routes/${routeId}/stops`),
  create: (data: { id: string; organization_id: string; code: string; name: string; direction: string }) =>
    fetcher<Route>('/routes', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  createVariant: (routeId: string, data: { id: string; name: string }) =>
    fetcher(`/routes/${routeId}/variants`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  addStopToVariant: (routeId: string, variantId: string, data: { stop_id: string; sequence_number: number; dwell_time_seconds: number }) =>
    fetcher(`/routes/${routeId}/variants/${variantId}/stops`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export const stops = {
  list: () => fetcher<{ items: Stop[] }>('/stops'),
  get: (stopId: string) => fetcher<Stop>(`/stops/${stopId}`),
  create: (data: { id: string; name: string; type: string; lat: number; lon: number; cash_allowed?: boolean; active?: boolean }) =>
    fetcher<Stop>('/stops', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (stopId: string, data: Partial<{ name: string; type: string; lat: number; lon: number; cash_allowed: boolean; active: boolean }>) =>
    fetcher<Stop>(`/stops/${stopId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  remove: (stopId: string) =>
    fetcher<{ status: string; stop_id: string }>(`/stops/${stopId}`, {
      method: 'DELETE',
    }),
};

export const organizations = {
  list: () => fetcher<{ items: { id: string; name: string; type: string; compliance_status: string; is_active: boolean }[] }>('/organizations'),
  create: (data: { name: string; type: string; compliance_status?: string; is_active?: boolean }) =>
    fetcher('/organizations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (organizationId: string, data: Partial<{ name: string; type: string; compliance_status: string; is_active: boolean }>) =>
    fetcher(`/organizations/${organizationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  remove: (organizationId: string) =>
    fetcher<{ status: string; organization_id: string }>(`/organizations/${organizationId}`, {
      method: 'DELETE',
    }),
};

export const vehicles = {
  list: (organizationId?: string) =>
    fetcher<{ items: { id: string; organization_id: string; plate_number: string; capacity: number; permit_number?: string | null; compliance_status: string; is_active: boolean }[] }>(
      organizationId ? `/vehicles?organization_id=${encodeURIComponent(organizationId)}` : '/vehicles'
    ),
  create: (data: { organization_id: string; plate_number: string; capacity?: number; permit_number?: string | null; compliance_status?: string; is_active?: boolean }) =>
    fetcher('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (vehicleId: string, data: Partial<{ organization_id: string; plate_number: string; capacity: number; permit_number?: string | null; compliance_status: string; is_active: boolean }>) =>
    fetcher(`/vehicles/${vehicleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

export const drivers = {
  list: (organizationId?: string) =>
    fetcher<{ items: Driver[] }>(
      organizationId ? `/drivers?organization_id=${encodeURIComponent(organizationId)}` : '/drivers'
    ),
  create: (data: { organization_id: string; user_id: string; full_name: string; phone: string; licence_number: string; pdp_verified?: boolean; is_active?: boolean }) =>
    fetcher('/drivers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (driverId: string, data: Partial<{ organization_id: string; full_name: string; phone: string; licence_number: string; pdp_verified: boolean; is_active: boolean }>) =>
    fetcher(`/drivers/${driverId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  remove: (driverId: string) =>
    fetcher<{ status: string; driver_id: string }>(`/drivers/${driverId}`, {
      method: 'DELETE',
    }),
};

// --- Bookings API ---

export const bookings = {
  quote: (tripId: string, originId: string, destId: string, partySize: number) =>
    fetcher('/bookings/quote', {
      method: 'POST',
      body: JSON.stringify({ trip_id: tripId, origin_stop_id: originId, destination_stop_id: destId, party_size: partySize }),
    }),
  create: (tripId: string, originId: string, destId: string, partySize: number) =>
    fetcher<Booking>('/bookings', {
      method: 'POST',
      body: JSON.stringify({ trip_id: tripId, origin_stop_id: originId, destination_stop_id: destId, party_size: partySize }),
    }),
  get: (bookingId: string) => fetcher<Booking>(`/bookings/${bookingId}`),
  pay: (bookingId: string, method: string, amount: number) =>
    fetcher(`/bookings/${bookingId}/pay`, {
      method: 'POST',
      body: JSON.stringify({ method, amount }),
    }),
  adminList: () => fetcher<{ items: Booking[] }>('/bookings/admin'),
  adminCreate: (data: { route_id: string; origin_stop_id: string; destination_stop_id: string; party_size: number; booking_channel?: string; passenger_id: string }) =>
    fetcher<{ booking: Booking }>('/bookings/admin', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  adminGet: (bookingId: string) => fetcher<{ booking: Booking }>(`/bookings/admin/${bookingId}`),
  adminCancel: (bookingId: string) =>
    fetcher<{ booking: Booking }>(`/bookings/admin/${bookingId}/cancel`, {
      method: 'POST',
    }),
};

// --- Trips & Operations API ---

export const trips = {
  list: (organizationId?: string) =>
    fetcher<{ items: Trip[] }>(organizationId ? `/trips?organization_id=${encodeURIComponent(organizationId)}` : '/trips'),
  adminList: () => fetcher<Trip[]>('/trips/admin'),
  create: (data: Partial<Trip>) =>
    fetcher<Trip>('/trips', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (tripId: string, data: Partial<Trip>) =>
    fetcher<Trip>(`/trips/admin/${tripId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  get: (tripId: string) => fetcher<Trip>(`/trips/${tripId}`),
  transition: (tripId: string, newState: string) =>
    fetcher<Trip>(`/trips/${tripId}/transition?new_state=${newState}`, {
      method: 'POST',
    }),
  start: (tripId: string) =>
    fetcher<Trip>(`/trips/${tripId}/transition?new_state=boarding`, {
      method: 'POST',
    }),
  depart: (tripId: string) =>
    fetcher<Trip>(`/trips/${tripId}/transition?new_state=enroute`, {
      method: 'POST',
    }),
};

export const users = {
  list: (organizationId?: string) =>
    fetcher<{ items: User[] }>(organizationId ? `/users?organization_id=${encodeURIComponent(organizationId)}` : '/users'),
  create: (data: { full_name: string; phone: string; password: string; role: UserRole; organization_id?: string | null; is_active?: boolean }) =>
    fetcher<User>('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (userId: string, data: Partial<{ full_name: string; phone: string; password: string; role: UserRole; organization_id: string | null; is_active: boolean }>) =>
    fetcher<User>(`/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  remove: (userId: string) =>
    fetcher<{ status: string; user_id: string }>(`/users/${userId}`, {
      method: 'DELETE',
    }),
};

export const qr = {
  scan: (tripId: string, qrTokenId: string) =>
    fetcher('/qr/scan', {
      method: 'POST',
      body: JSON.stringify({ trip_id: tripId, qr_token_id: qrTokenId }),
    }),
};

export const rank = {
  issueTicket: (rankId: string, tripId?: string) =>
    fetcher('/rank/tickets', {
      method: 'POST',
      body: JSON.stringify(tripId ? { rank_id: rankId, trip_id: tripId } : { rank_id: rankId }),
    }),
  assignTicket: (ticketId: string, tripId: string) =>
    fetcher('/rank/tickets/assign', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, trip_id: tripId }),
    }),
  boardTicket: (ticketId: string) =>
    fetcher(`/rank/tickets/${ticketId}/board`, {
      method: 'POST',
    }),
};
