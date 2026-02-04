import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import App from './App';
import Admin from './Admin';
import ScannerTest from './ScannerTest';
import BulkEPCISCreation from './BulkEPCISCreation';
import AuthWrapper from './AuthWrapper';

// Wrapper component for BulkEPCISCreation that handles auth
const BulkEPCISWrapper = () => {
  const handleBack = () => {
    window.location.href = '/';
  };
  
  return (
    <AuthWrapper>
      <BulkEPCISCreation onBack={handleBack} />
    </AuthWrapper>
  );
};

const AppRouter = () => {
  // Simple routing based on URL path
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);
  
  const isAdminPath = currentPath.startsWith('/admin');
  const isScannerTestPath = currentPath.startsWith('/scanner-test');
  const isBulkEPCISPath = currentPath.startsWith('/epcis/bulk-create');

  return (
    <>
      {isScannerTestPath ? (
        <ScannerTest />
      ) : isAdminPath ? (
        <Admin />
      ) : isBulkEPCISPath ? (
        <AuthProvider>
          <BulkEPCISWrapper />
        </AuthProvider>
      ) : (
        <AuthProvider>
          <App />
        </AuthProvider>
      )}
    </>
  );
};

export default AppRouter;