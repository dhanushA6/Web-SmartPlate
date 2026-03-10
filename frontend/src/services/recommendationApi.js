import { api } from "../api/apiClient";

export const getFoodRecommendation = (data) =>
  api.post("/api/recommend-food", data);

export const sendFoodFeedback = (data) =>
  api.post("/api/food-feedback", data);

