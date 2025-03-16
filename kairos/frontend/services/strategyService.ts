import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface StrategyParams {
  fast_period: number;
  slow_period: number;
  signal_period: number;
}

export interface Strategy {
  id?: string;
  name: string;
  stock_code: string;
  stock_name: string;
  strategy_type: string;
  params: StrategyParams;
  take_profit: number;
  stop_loss: number;
  investment_amount: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export const strategyService = {
  async getStrategies(): Promise<Strategy[]> {
    const response = await axios.get(`${API_URL}/strategies`);
    return response.data;
  },

  async getStrategy(id: string): Promise<Strategy> {
    const response = await axios.get(`${API_URL}/strategies/${id}`);
    return response.data;
  },

  async createStrategy(strategy: Strategy): Promise<Strategy> {
    const response = await axios.post(`${API_URL}/strategies`, strategy);
    return response.data;
  },

  async updateStrategy(id: string, strategy: Strategy): Promise<Strategy> {
    const response = await axios.put(`${API_URL}/strategies/${id}`, strategy);
    return response.data;
  },

  async deleteStrategy(id: string): Promise<void> {
    await axios.delete(`${API_URL}/strategies/${id}`);
  }
}; 