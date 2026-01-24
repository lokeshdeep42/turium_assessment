import { useState } from 'react';
import IngestForm from './components/IngestForm';
import ItemsList from './components/ItemsList';
import QueryInterface from './components/QueryInterface';
import './App.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleIngestSuccess = () => {
    // Trigger refresh of items list
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧠 AI Knowledge Inbox</h1>
        <p>Save notes and URLs, then ask questions powered by AI</p>
      </header>

      <main className="app-main">
        <div className="top-section">
          <IngestForm onIngestSuccess={handleIngestSuccess} />
          <QueryInterface />
        </div>

        <ItemsList refreshTrigger={refreshTrigger} />
      </main>

      <footer className="app-footer">
        <p>Built with FastAPI, React, and Google Gemini AI</p>
      </footer>
    </div>
  );
}

export default App;
