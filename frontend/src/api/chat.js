import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

/**
 * Send a message to the RAG chatbot backend.
 * @param {string} message  - User's question text
 * @param {string} sessionId - Session ID for conversation tracking
 * @returns {Promise<{ answer, sources, session_id, response_time_ms, pii_detected }>}
 */
export async function sendChatMessage(message, sessionId) {
  const response = await apiClient.post('/api/chat', {
    message,
    session_id: sessionId,
  });
  return response.data;
}

/**
 * Get the health status of the backend.
 * @returns {Promise<{ status, chroma_document_count, knowledge_base_loaded }>}
 */
export async function getHealth() {
  const response = await apiClient.get('/api/health');
  return response.data;
}
