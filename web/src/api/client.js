// =============================================================
// client.js — jedini sloj koji priča s backendom (fetch wrapper)
// =============================================================
// Radi tri stvari za SVE pozive:
//  1. Dodaje "Authorization: Bearer <access_token>" header.
//  2. Ako backend vrati 401 -> pokuša OSVJEŽITI token (/auth/refresh)
//     i ponovi isti zahtjev, jednom. Ovo je "interceptor".
//  3. Sve greške pretvara u ApiError s čitljivom porukom.
import { clearTokens, getTokens, setTokens } from './tokens'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(status, code, message, errors = []) {
    super(message)
    this.status = status
    this.code = code
    this.errors = errors // [{field, message}] kod validacijskih (422) grešaka
  }
}

// Kad sesija definitivno istekne (refresh ne uspije), pozovemo ovaj callback.
// Registrira ga main.js (odjavi korisnika i preusmjeri na login).
let onSessionExpired = () => {}
export function setSessionExpiredHandler(fn) {
  onSessionExpired = fn
}

// Ako 5 zahtjeva istovremeno dobije 401, refresh šaljemo SAMO JEDNOM,
// a ostali čekaju isti promise.
let refreshPromise = null
function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const { refresh } = getTokens()
      if (!refresh) throw new Error('nema refresh tokena')
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
      if (!res.ok) throw new Error('refresh nije uspio')
      const data = await res.json()
      setTokens(data.access_token, data.refresh_token)
    })().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export async function request(path, { method = 'GET', body, auth = true } = {}, retried = false) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const { access } = getTokens()
    if (access) headers.Authorization = `Bearer ${access}`
  }

  let res
  try {
    res = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'network_error', 'Server nije dostupan. Provjeri vezu i pokušaj ponovno.')
  }

  if (res.status === 401 && auth) {
    if (!retried) {
      try {
        await refreshAccessToken()
      } catch {
        clearTokens()
        onSessionExpired()
        throw new ApiError(401, 'session_expired', 'Sesija je istekla. Prijavi se ponovno.')
      }
      return request(path, { method, body, auth }, true) // ponovi zahtjev s novim tokenom
    }
    clearTokens()
    onSessionExpired()
    throw new ApiError(401, 'session_expired', 'Sesija je istekla. Prijavi se ponovno.')
  }

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new ApiError(
      res.status,
      data?.code ?? 'error',
      data?.message ?? 'Došlo je do greške na serveru.',
      data?.errors ?? [],
    )
  }
  return data
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body: body ?? undefined }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
}
