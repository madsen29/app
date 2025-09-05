import React from 'react';
import { AuthProvider } from './AuthContext';
import App from './App';
import Admin from './Admin';
import ScannerTest from './ScannerTest';

const AppRouter = () => {
  // Simple routing based on URL path
  const isAdminPath = window.location.pathname.startsWith('/admin');

  return (
    <>
      {isAdminPath ? (
        <Admin />
      ) : (
        <AuthProvider>
          <App />
        </AuthProvider>
      )}
    </>
  );
};

export default AppRouter;