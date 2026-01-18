import axios from 'axios';
import { z } from 'zod';
import {
  InsightSchema,
  InsightListResponseSchema,
  type Insight,
  type InsightListResponse,
  type FetchInsightsParams,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Fetch paginated list of insights with optional filters
 */
export async function fetchInsights(
  params: FetchInsightsParams = {}
): Promise<InsightListResponse> {
  const { data } = await apiClient.get('/api/insights', { params });
  return InsightListResponseSchema.parse(data);
}

/**
 * Fetch single insight by ID
 */
export async function fetchInsightById(id: string): Promise<Insight> {
  const { data } = await apiClient.get(`/api/insights/${id}`);
  return InsightSchema.parse(data);
}

/**
 * Fetch daily top 5 insights
 */
export async function fetchDailyTop(limit: number = 5): Promise<Insight[]> {
  const { data } = await apiClient.get('/api/insights/daily-top', {
    params: { limit },
  });
  return z.array(InsightSchema).parse(data);
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const { data } = await apiClient.get('/health');
  return data;
}
