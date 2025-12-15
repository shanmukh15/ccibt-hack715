import React, { useState } from 'react';

interface LoginProps {
  onLogin: (username: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      onLogin(username.trim());
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Welcome to Fargo Funda</h2>
        <p></p>
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Howdy!! What's your name?"
            className="login-input"
            autoFocus
          />
          <button type="submit" className="login-button" disabled={!username.trim()}>
            Assist Me
          </button>
        </form>
      </div>
    </div>
  );
};
