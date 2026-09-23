// Spremanje tokena u localStorage (preživi refresh stranice).
// Kompromis: localStorage je dostupan JavaScriptu, pa ga XSS napad može pročitati.
// Sigurnija (ali složenija) alternativa je httpOnly cookie koji postavlja backend.
const ACCESS = 'access_token'
const REFRESH = 'refresh_token'

export function getTokens() {
  return { access: localStorage.getItem(ACCESS), refresh: localStorage.getItem(REFRESH) }
}

export function setTokens(access, refresh) {
  localStorage.setItem(ACCESS, access)
  localStorage.setItem(REFRESH, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS)
  localStorage.removeItem(REFRESH)
}
