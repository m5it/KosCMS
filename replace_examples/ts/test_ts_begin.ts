import type { User, Config } from './types';
import { fetchApi } from './api';

interface Service<T> {
  getAll(): Promise<T[]>;
  getById(id: string): Promise<T | null>;
}

const CONFIG: Config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000
};

export class UserService implements Service<User> {
  async getAll(): Promise<User[]> {
    return fetchApi('/users');
  }
  
  async getById(id: string): Promise<User | null> {
    return fetchApi(`/users/${id}`);
  }
}

export default UserService;