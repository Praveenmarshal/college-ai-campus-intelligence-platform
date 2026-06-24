/**
 * api/services.js
 * All API calls organised by domain.
 * Each function returns an Axios promise.
 */

import apiClient, { uploadFile } from './client'

// ── Auth ──────────────────────────────────────────────────
export const authAPI = {
  login:       (credentials) => apiClient.post('/api/auth/login', credentials),
  googleLogin: (credential)  => apiClient.post('/api/auth/google', { credential }),
  register:    (data)        => apiClient.post('/api/auth/register', data),
  logout:      ()            => apiClient.post('/api/auth/logout'),
  refresh:     (token)       => apiClient.post('/api/auth/refresh', { refresh_token: token }),
  me:          ()            => apiClient.get('/api/auth/me'),
  changePassword: (data)     => apiClient.put('/api/auth/change-password', data),
}

// ── Users ──────────────────────────────────────────────────
export const usersAPI = {
  getAll:   (params)     => apiClient.get('/api/users', { params }),
  getById:  (id)         => apiClient.get(`/api/users/${id}`),
  update:   (id, data)   => apiClient.put(`/api/users/${id}`, data),
  delete:   (id)         => apiClient.delete(`/api/users/${id}`),
  updateProfile: (data)  => apiClient.put('/api/users/profile', data),
  uploadAvatar:  (file)  => uploadFile('/api/users/avatar', file),
}

// ── Documents ──────────────────────────────────────────────
export const documentsAPI = {
  uploadPDF:   (file, data, onProg) => uploadFile('/api/documents/upload/pdf', file, data, onProg),
  uploadExcel: (file, data, onProg) => uploadFile('/api/documents/upload/excel', file, data, onProg),
  uploadCSV:   (file, data, onProg) => uploadFile('/api/documents/upload/csv', file, data, onProg),
  getAll:      (params)             => apiClient.get('/api/documents', { params }),
  getById:     (id)                 => apiClient.get(`/api/documents/${id}`),
  delete:      (id)                 => apiClient.delete(`/api/documents/${id}`),
  reprocess:   (id)                 => apiClient.post(`/api/documents/${id}/reprocess`),
}

// ── Chat ──────────────────────────────────────────────────
export const chatAPI = {
  sendMessage:    (data)       => apiClient.post('/api/chat/message', data),
  getSessions:    ()           => apiClient.get('/api/chat/sessions'),
  getSession:     (id)         => apiClient.get(`/api/chat/sessions/${id}`),
  deleteSession:  (id)         => apiClient.delete(`/api/chat/sessions/${id}`),
  clearHistory:   ()           => apiClient.delete('/api/chat/sessions'),
}

// ── Analytics ──────────────────────────────────────────────
export const analyticsAPI = {
  getDashboard:   ()      => apiClient.get('/api/analytics/dashboard'),
  getAttendance:  (params)=> apiClient.get('/api/analytics/attendance', { params }),
  getPlacements:  (params)=> apiClient.get('/api/analytics/placements', { params }),
  getAcademic:    (params)=> apiClient.get('/api/analytics/academic', { params }),
  getSystemStats: ()      => apiClient.get('/api/analytics/system'),
}

// ── Students ───────────────────────────────────────────────
export const studentsAPI = {
  getAll:      (params)    => apiClient.get('/api/students', { params }),
  getById:     (id)        => apiClient.get(`/api/students/${id}`),
  create:      (data)      => apiClient.post('/api/students', data),
  update:      (id, data)  => apiClient.put(`/api/students/${id}`, data),
  delete:      (id)        => apiClient.delete(`/api/students/${id}`),
  getMyProfile:()          => apiClient.get('/api/students/me'),
  uploadBulk:  (file, onP) => uploadFile('/api/students/bulk-upload', file, {}, onP),
}

// ── Faculty ────────────────────────────────────────────────
export const facultyAPI = {
  getAll:   (params)    => apiClient.get('/api/faculty', { params }),
  getById:  (id)        => apiClient.get(`/api/faculty/${id}`),
  create:   (data)      => apiClient.post('/api/faculty', data),
  update:   (id, data)  => apiClient.put(`/api/faculty/${id}`, data),
  delete:   (id)        => apiClient.delete(`/api/faculty/${id}`),
  getMyProfile: ()      => apiClient.get('/api/faculty/me'),
}

// ── Notifications ──────────────────────────────────────────
export const notificationsAPI = {
  getAll:       (params)   => apiClient.get('/api/notifications', { params }),
  markRead:     (id)       => apiClient.put(`/api/notifications/${id}/read`),
  markAllRead:  ()         => apiClient.put('/api/notifications/read-all'),
  delete:       (id)       => apiClient.delete(`/api/notifications/${id}`),
  getUnreadCount: ()       => apiClient.get('/api/notifications/unread-count'),
  getPreferences: ()       => apiClient.get('/api/notifications/preferences'),
  updatePreferences:(data) => apiClient.put('/api/notifications/preferences', data),
}

// ── Health ─────────────────────────────────────────────────
export const healthAPI = {
  check: () => apiClient.get('/api/health'),
  ping:  () => apiClient.get('/api/health/ping'),
}

// ── Machine Learning ───────────────────────────────────────
export const mlAPI = {
  predictAll:       (studentId) => apiClient.get(`/api/ml/predict/${studentId}`),
  predictAttendance:(studentId) => apiClient.get(`/api/ml/predict/attendance/${studentId}`),
  predictCgpa:      (studentId) => apiClient.get(`/api/ml/predict/cgpa/${studentId}`),
  predictPlacement: (studentId) => apiClient.get(`/api/ml/predict/placement/${studentId}`),
  predictFeeDefault:(studentId) => apiClient.get(`/api/ml/predict/fee-default/${studentId}`),
  trainModels:      ()          => apiClient.post('/api/ml/train'),
  atRiskStudents:   ()          => apiClient.get('/api/ml/at-risk-students'),
}

// ── Smart Router / Multi-Agent ──────────────────────────────
export const routerAPI = {
  ask:        (data) => apiClient.post('/api/router/ask', data),
  askHybrid:  (data) => apiClient.post('/api/router/ask-hybrid', data),
  listAgents: ()     => apiClient.get('/api/router/agents'),
}

// ── Resume ───────────────────────────────────────────────────
export const resumeAPI = {
  analyze: (file, targetRole, onProg) => uploadFile('/api/resume/analyze', file, { target_role: targetRole || '' }, onProg),
  get:     (id) => apiClient.get(`/api/resume/${id}`),
}

// ── OCR / Question Paper ───────────────────────────────────
export const ocrAPI = {
  extract:            (file, onProg) => uploadFile('/api/ocr/extract', file, {}, onProg),
  analyzeQuestionPaper: (file, onProg) => uploadFile('/api/ocr/question-paper/analyze', file, {}, onProg),
}

// ── MongoDB NL Query ────────────────────────────────────────
export const mongoQueryAPI = {
  collections: () => apiClient.get('/api/mongo-query/collections'),
  ask:         (data) => apiClient.post('/api/mongo-query/ask', data),
}

// ── Excel ─────────────────────────────────────────────────
export const excelAPI = {
  upload:  (file, data, onProg) => uploadFile('/api/excel/upload', file, data, onProg),
  getAll:  ()                   => apiClient.get('/api/excel'),
  getById: (id)                 => apiClient.get(`/api/excel/${id}`),
  query:   (id, data)           => apiClient.post(`/api/excel/${id}/query`, data),
}

// ── CSV ───────────────────────────────────────────────────
export const csvAPI = {
  upload:  (file, data, onProg) => uploadFile('/api/csv/upload', file, data, onProg),
  getAll:  ()                   => apiClient.get('/api/csv'),
  query:   (id, data)           => apiClient.post(`/api/csv/${id}/query`, data),
}
