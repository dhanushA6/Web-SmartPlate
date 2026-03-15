import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const registerUser = (data) => api.post('/auth/register', data);

export const loginUser = (data) => api.post('/auth/login', data);

export const getProfile = (userId) => api.get(`/profile/${userId}`);

export const updateProfile = (payload) => api.post('/profile/update', payload);

export const uploadMedicalReport = (userId, file) => {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('file', file);

  return axios.post(`${baseURL}/profile/upload-medical-report`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

export const predictNutrition = (userId) =>
  api.post('/nutrition/predict-nutrition', null, {
    params: { user_id: userId }
  });

export const askAssistant = (payload) => api.post('/ask-assistant', payload);

// Image-based multi-food detection
export const detectFoodsFromImage = (file) => {
  const formData = new FormData();
  formData.append('file', file);

  return axios.post(`${baseURL}/suitability/detect-foods`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Nutrition retrieval for manually entered foods only
export const fetchFoodNutrition = (foodName) =>
  api.get('/suitability/food-nutrition', {
    params: { food_name: foodName }
  });

// Meal-level suitability evaluation
export const checkSuitability = (payload) => api.post('/suitability/check-meal', payload);


