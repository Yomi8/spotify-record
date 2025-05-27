import { useUser } from '/UserContext';
import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children }) {
  const { isLoggedIn } = useUser();

  return isLoggedIn ? children : <Navigate to="/signin" replace />;
}