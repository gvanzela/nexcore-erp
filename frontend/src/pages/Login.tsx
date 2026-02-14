// Simple Login screen (visual only)
// No API calls yet
// This file exists only to shape the UI and navigation flow

import { useState } from 'react'
import { login } from '../api/client'
import { useNavigate } from "react-router-dom"

// Real login screen
// Calls backend and stores tokens
function Login() {
  // Local state for form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // Handles login click
  async function handleLogin() {
    console.log(email, password)
    
    try {
      setError(null)

      // Call backend login endpoint
      const data = await login(email, password)

      // Persist tokens locally
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      // For now: just confirm success
      console.log('Logged in successfully')
      navigate("/")
      // Later: redirect to Orders page
    } catch (err) {
      // Any error = invalid credentials or server error
      setError('Invalid email or password')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div style={{ padding: 24, maxWidth: 400, width: '100%' }}>
        <h2>Login</h2>

        {/* Error message */}
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {/* Email input */}
        <div style={{ marginBottom: 12 }}>
          <label>Email</label>
          <br />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: 8 }}
          />
        </div>

        {/* Password input */}
        <div style={{ marginBottom: 12 }}>
          <label>Password</label>
          <br />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: 8 }}
          />
        </div>

        {/* Login button */}
        <button
          onClick={handleLogin}
          style={{ padding: 10, width: '100%' }}
        >
          Sign in
        </button>
      </div>
    </div>
  )
}

export default Login