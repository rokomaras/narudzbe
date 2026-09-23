// Klijentska validacija (brza povratna informacija prije slanja).
// Backend ionako ponovno validira: ovo je samo UX, nikad sigurnost.

export function validateRegister(f) {
  const e = {}
  if (!/^[A-Za-z0-9_.-]{3,50}$/.test(f.username)) e.username = 'Najmanje 3 znaka: slova, brojevi, . _ -'
  if (f.password.length < 6) e.password = 'Lozinka mora imati najmanje 6 znakova'
  if (f.password.length > 72) e.password = 'Lozinka može imati najviše 72 znaka'
  if (f.full_name.trim().length < 2) e.full_name = 'Unesi ime i prezime'
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email)) e.email = 'Unesi ispravnu email adresu'
  return e
}

// Pretvara serversku validacijsku grešku u objekt {polje: poruka}.
export function serverFieldErrors(err) {
  const out = {}
  for (const item of err?.errors ?? []) {
    if (item.field && !out[item.field]) out[item.field] = item.message
  }
  return out
}
