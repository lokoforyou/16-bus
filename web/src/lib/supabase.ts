type Filter = Record<string, string | number | boolean>;

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const configured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

function headers() {
  if (!configured) {
    throw new Error('Supabase is not configured');
  }

  return {
    apikey: SUPABASE_ANON_KEY as string,
    Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json',
    Prefer: 'return=representation',
  };
}

function queryFrom(filter?: Filter) {
  if (!filter) {
    return '';
  }
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filter)) {
    params.set(key, `eq.${value}`);
  }
  const query = params.toString();
  return query ? `?${query}` : '';
}

async function request<T>(path: string, init: RequestInit = {}) {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: {
      ...headers(),
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
    throw new Error(payload.message || payload.details || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function isSupabaseConfigured() {
  return configured;
}

export const supabaseDb = {
  list: <T>(table: string, filter?: Filter) => request<T[]>(`${table}?select=*${queryFrom(filter)}`),
  create: <T>(table: string, data: Record<string, unknown>) =>
    request<T[]>(table, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: <T>(table: string, idField: string, idValue: string, data: Record<string, unknown>) =>
    request<T[]>(`${table}?${idField}=eq.${encodeURIComponent(idValue)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  remove: <T>(table: string, idField: string, idValue: string) =>
    request<T[]>(`${table}?${idField}=eq.${encodeURIComponent(idValue)}`, {
      method: 'DELETE',
    }),
};
