import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export const getStats = () => api.get('/stats').then(r => r.data)

export const getIndicators = (params = {}) =>
  api.get('/indicators', { params }).then(r => r.data)

export const getIndicator = (id) =>
  api.get(`/indicators/${id}`).then(r => r.data)

export const getAlerts = (params = {}) =>
  api.get('/alerts', { params }).then(r => r.data)

export const acknowledgeAlert = (id) =>
  api.post(`/alerts/${id}/acknowledge`).then(r => r.data)

export const triggerIngest = () =>
  api.post('/ingest').then(r => r.data)

export const triggerRetrain = () =>
  api.post('/retrain').then(r => r.data)

export default api
