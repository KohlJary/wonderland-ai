export interface Note {
  id: number;
  title: string;
  body: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateNoteRequest {
  title: string;
  body: string;
  tags?: string[];
}

export interface UpdateNoteRequest {
  title?: string;
  body?: string;
  tags?: string[];
}

export interface TagListResponse {
  tags: string[];
}

const API_BASE = '/api';

export const api = {
  async createNote(note: CreateNoteRequest): Promise<Note> {
    const response = await fetch(`${API_BASE}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(note),
    });
    if (!response.ok) throw new Error('Failed to create note');
    return response.json();
  },

  async listNotes(search?: string, tag?: string): Promise<Note[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tag) params.append('tag', tag);
    const response = await fetch(`${API_BASE}/notes?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to list notes');
    return response.json();
  },

  async getNote(id: number): Promise<Note> {
    const response = await fetch(`${API_BASE}/notes/${id}`);
    if (!response.ok) throw new Error('Failed to get note');
    return response.json();
  },

  async updateNote(id: number, update: UpdateNoteRequest): Promise<Note> {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    });
    if (!response.ok) throw new Error('Failed to update note');
    return response.json();
  },

  async deleteNote(id: number): Promise<void> {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete note');
  },

  async getAllTags(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/tags`);
    if (!response.ok) throw new Error('Failed to get tags');
    const data: TagListResponse = await response.json();
    return data.tags;
  },
};
