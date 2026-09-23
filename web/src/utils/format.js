// Cijene su na backendu u centima (integer). Ovdje ih pretvaramo za prikaz.
export function formatEuro(cents) {
  return (cents / 100).toLocaleString('hr-HR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

// "19,99" ili "19.99" -> 1999 ; nevaljano -> NaN
export function eurosToCents(text) {
  const n = Number(String(text).trim().replace(',', '.'))
  return Number.isFinite(n) ? Math.round(n * 100) : NaN
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('hr-HR', { dateStyle: 'short', timeStyle: 'short' })
}

export const STATUS_LABELS = {
  pending: 'Čeka plaćanje',
  paid: 'Plaćeno',
  shipped: 'Poslano',
  delivered: 'Dostavljeno',
  cancelled: 'Otkazano',
}
