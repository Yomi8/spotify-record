import { useNavigate } from 'react-router-dom';
import { useUser } from '../components/UserContext';


export default function SignIn() {
  const { login } = useUser();
  const navigate = useNavigate();

  const handleLogin = async () => {
    // simulate real API call
    const fakeJWT = 'mock-jwt-token';
    login(fakeJWT);
    navigate('/profile'); // redirect on success
  };

  return (
    <div className="container mt-5 text-white">
      <h2>Sign In</h2>
      <button className="btn btn-primary" onClick={handleLogin}>
        Sign In
      </button>
    </div>
  );
}