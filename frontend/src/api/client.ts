// Base URL of the backend API (FastAPI)
const API_URL = 'http://localhost:8000/api/v1'

// Login request
// Sends email + password to the backend
// Returns tokens if credentials are valid
export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      // We are sending JSON data
      'Content-Type': 'application/json',
    },
    // Payload expected by the backend
    body: JSON.stringify({ email, password }),
  })

  // If backend returns 401 / 400
  if (!response.ok) {
    throw new Error('Invalid credentials')
  }

  // Expected response:
  // { access_token: string, refresh_token: string }
  return response.json()
}
