import { apiRequest } from '@/lib/api'

export function useAssistantAdmin() {
  return {
    listKnowledge: (query) => apiRequest('/asistente/conocimiento/', { query }),
    createKnowledge: (body) => apiRequest('/asistente/conocimiento/', { method: 'POST', body }),
    updateKnowledge: (id, body) => apiRequest(`/asistente/conocimiento/${id}/`, { method: 'PATCH', body }),
    activateKnowledge: (id) => apiRequest(`/asistente/conocimiento/${id}/activar/`, { method: 'POST', body: {} }),
    deactivateKnowledge: (id) => apiRequest(`/asistente/conocimiento/${id}/desactivar/`, { method: 'POST', body: {} }),
    listUnresolved: (query) => apiRequest('/asistente/no-resueltas/', { query }),
    resolveUnresolved: (id) => apiRequest(`/asistente/no-resueltas/${id}/resolver/`, { method: 'POST', body: {} }),
    ignoreUnresolved: (id) => apiRequest(`/asistente/no-resueltas/${id}/ignorar/`, { method: 'POST', body: {} }),
    createArticleFromUnresolved: (id, body) => apiRequest(`/asistente/no-resueltas/${id}/crear-articulo/`, { method: 'POST', body }),
    getConfig: () => apiRequest('/asistente/configuracion/'),
    updateConfig: (body) => apiRequest('/asistente/configuracion/', { method: 'PATCH', body }),
  }
}
