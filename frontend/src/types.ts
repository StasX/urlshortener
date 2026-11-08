export interface User {
  id: string
  first_name: string
  last_name: string
  email: string
}

export interface ShortLink {
  id: string
  shortUrl: string
  fullUrl: string
  visits: number
}

export interface AuthForm {
  firstName: string
  lastName: string
  email: string
  password: string
  repeatPassword: string
}

export interface AuthResponse { user: User | null }
export interface LinkResponse { url: string }
