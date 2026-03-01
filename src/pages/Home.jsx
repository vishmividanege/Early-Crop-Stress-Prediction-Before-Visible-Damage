// src/pages/Home.jsx
import React from 'react'
import { Link } from 'react-router-dom'
import riceFieldImage from '../assets/image7.jpeg' // your file name

export default function Home() {
  return (
    <div
      style={{
        minHeight: '100vh',
        height: '100vh',
        backgroundColor: '#0f172a',
        backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.4)), url(${riceFieldImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        color: '#f8fafc',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: '1.5rem 5%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          
          
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
        }}
      >
        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
          <span style={{ color: '#1d7327' }}>Agri</span>Guard AI
        </div>

        <div style={{ display: 'flex', gap: '1.4rem' }}>
          <Link to="/login" style={navBtn}>Login</Link>
          <Link to="/signup" style={{ ...navBtn, ...primaryBtn }}>Sign Up</Link>
          <Link to="/about" style={navBtn}>About Us</Link>
        </div>
      </header>

      {/* Hero */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          padding: '0 5%',
          marginTop: '90px',
        }}
      >
        <h1
          style={{
            fontSize: 'clamp(3.5rem, 8vw, 6rem)',
            fontWeight: 430,
            margin: '0 0 1.5rem',
            lineHeight: 1,
            color: "#2a4f2e",
            
          }}
        >
          AgriGuard AI —<br />
          Crop Stress Predictor
        </h1>

        <p
          style={{
            fontSize: 'clamp(1.25rem, vw, 1.6rem)',
            maxWidth: '700px',
            margin: '0 0 3rem',
            lineHeight: 1.6,
            color: "hsl(127, 71%, 23%)"


          }}
        >
          Use the power of artificial intelligence to monitor crop health and detect stress early.<br />
          Our smart platform analyzes satellite data to help farmers make faster,<br />
          data-driven decisions and improve productivity.
        </p>

        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link to="/signup" style={ctaPrimary}>Get Started — Free</Link>
          <Link to="/login" style={ctaOutline}>Login to Dashboard</Link>
        </div>
      </main>

      <footer style={{ padding: '2rem', textAlign: 'center', opacity: 0.8 }}>
        © {new Date().getFullYear()} AgriGuard AI
      </footer>
    </div>
  )
}

// Button styles
const navBtn = {
  padding: '0.75rem 1.8rem',
  borderRadius: '999px',
  background: 'rgba(255,255,255,0.1)',
  color: '#ffffff',
  textDecoration: 'none',
  fontWeight: 500,
  border: '1px solid rgba(255,255,255,0.3)',
}

const primaryBtn = {
  background: 'hsl(128, 55%, 29%)',
 
  fontWeight: 600,
}

const ctaPrimary = {
   padding: '1.2rem 2.8rem',
  border: '2px solid #ffffff',
  borderRadius: '999px',
  color: '#ffffff',
  fontSize: '1.2rem',
  fontWeight: 500,
  textDecoration: 'none',
}

const ctaOutline = {
  padding: '1.2rem 2.8rem',
  border: '2px solid #ffffff',
  borderRadius: '999px',
  color: '#ffffff',
  fontSize: '1.2rem',
  fontWeight: 500,
  textDecoration: 'none',
}