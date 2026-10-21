import { HealthStatus } from '@/components/HealthStatus';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Nexus Console</h1>
        <p className="subtitle">The open alternative to Salesforce, designed for AI</p>
        <HealthStatus />
      </header>
      <main className="app-main">
        <section className="hero" aria-labelledby="hero-title">
          <h2 id="hero-title">Welcome to Nexus Console</h2>
          <p>
            An AI-powered CRM platform built for developers. Manage contacts, companies, and opportunities
            with intelligent enrichment and automation.
          </p>
          <div className="feature-grid">
            <article className="feature-card">
              <h3>Contacts & Companies</h3>
              <p>Rich profiles with AI enrichment from multiple data sources</p>
            </article>
            <article className="feature-card">
              <h3>Opportunities</h3>
              <p>Pipeline management with predictive scoring</p>
            </article>
            <article className="feature-card">
              <h3>AI Enrichment</h3>
              <p>Deterministic offline + optional LLM-powered data enhancement</p>
            </article>
          </div>
        </section>
      </main>
      <footer className="app-footer">
        <p>Nexus Console © 2024 Ryan Vo</p>
      </footer>
    </div>
  );
}

export default App;