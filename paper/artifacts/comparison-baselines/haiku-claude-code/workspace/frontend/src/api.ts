import axios from 'axios'

const API_BASE_URL = '/api'

export interface Tag {
  id: number
  name: string
}

export interface Note {
  id: number
  title: string
  body: string
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface NoteCreate {
  title: string
  body: string
  tags: string[]
}

export interface NoteUpdate {
  title: string
  body: string
  tags: string[]
}

const client = axios.create({
  baseURL: API_BASE_URL,
})

export const notesApi = {
  listNotes: (filters?: { tag?: string; search?: string }) => {
    return client.get<Note[]>('/notes', { params: filters })
  },

  getNote: (id: number) => {
    return client.get<Note>(`/notes/${id}`)
  },

  createNote: (data: NoteCreate) => {
    return client.post<Note>('/notes', data)
  },

  updateNote: (id: number, data: NoteUpdate) => {
    return client.put<Note>(`/notes/${id}`, data)
  },

  deleteNote: (id: number) => {
    return client.delete(`/notes/${id}`)
  },

  listTags: () => {
    return client.get<Tag[]>('/tags')
  },
}
