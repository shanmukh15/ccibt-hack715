import React, { useState } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Login } from './components/Login';

function App() {
  const [user, setUser] = useState<string | null>(null);

  const handleLogin = (username: string) => {
    setUser(username);
  };

  return (
    <div className="app-container">
      <div className="background-gradient"></div>
      <main className="main-content">
        {user ? <ChatInterface user={user} /> : <Login onLogin={handleLogin} />}
      </main>
    </div>
  );
}

export default App;
