import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthWrapper = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        {isLoginMode ? (
          <LoginForm onSwitchToRegister={() => setIsLoginMode(false)} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setIsLoginMode(true)} />
        )}
      </>
    );
  }

  return children;
};

export default AuthWrapper;