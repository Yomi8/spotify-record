import { useUser } from './UserContext';
import { Navigate } from 'react-router-dom';
import React from 'react';

export default function ProtectedRoute({ children }: React.PropsWithChildren) {
  const { isLoggedIn } = useUser();

  return isLoggedIn ? children : <Navigate to="/signin" replace />;
}