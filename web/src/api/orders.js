import { api } from './client'

export const ordersApi = {
  list: (status) => api.get(status ? `/orders?status=${encodeURIComponent(status)}` : '/orders'),
  get: (id) => api.get(`/orders/${id}`),
  create: (payload) => api.post('/orders', payload),
  pay: (id) => api.post(`/orders/${id}/pay`),
  cancel: (id) => api.post(`/orders/${id}/cancel`),
  ship: (id) => api.post(`/orders/${id}/ship`),
  deliver: (id) => api.post(`/orders/${id}/deliver`),
  addItem: (id, productId, quantity) =>
    api.post(`/orders/${id}/items`, { product_id: productId, quantity }),
  updateItem: (id, itemId, quantity) => api.patch(`/orders/${id}/items/${itemId}`, { quantity }),
  removeItem: (id, itemId) => api.delete(`/orders/${id}/items/${itemId}`),
}
