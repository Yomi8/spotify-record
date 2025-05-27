import { useUser } from '../components/UserContext';

export default function Profile() {
  const { logout } = useUser();

  return (
    <div className="container mt-5 text-white">
      <h2>Welcome to your profile!</h2>
      <button className="btn btn-danger mt-3" onClick={logout}>
        Logout
      </button>
    </div>
  );
}