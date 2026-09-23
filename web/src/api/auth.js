import { api } from './client'

export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }, { auth: false }),
  register: (payload) => api.post('/auth/register', payload, { auth: false }),
  me: () => api.get('/auth/me'),
}
