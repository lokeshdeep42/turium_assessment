import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Error interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
        console.error('API Error:', errorMessage);
        throw new Error(errorMessage);
    }
);

export const ingestContent = async (content, sourceType) => {
    const response = await api.post('/ingest', {
        content,
        source_type: sourceType,
    });
    return response.data;
};

export const getItems = async (sourceType = null) => {
    const params = sourceType ? { source_type: sourceType } : {};
    const response = await api.get('/items', { params });
    return response.data;
};

export const getItem = async (itemId) => {
    const response = await api.get(`/items/${itemId}`);
    return response.data;
};

export const deleteItem = async (itemId) => {
    const response = await api.delete(`/items/${itemId}`);
    return response.data;
};

export const queryKnowledgeBase = async (question, maxResults = 5) => {
    const response = await api.post('/query', {
        question,
        max_results: maxResults,
    });
    return response.data;
};

export const healthCheck = async () => {
    const response = await api.get('/health');
    return response.data;
};

export default api;
