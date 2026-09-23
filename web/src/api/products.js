import { api } from './client'

export const productsApi = {
  list: () => api.get('/products'),
  get: (id) => api.get(`/products/${id}`),
  create: (payload) => api.post('/products', payload),
  update: (id, payload) => api.patch(`/products/${id}`, payload),
  remove: (id) => api.delete(`/products/${id}`),
}
