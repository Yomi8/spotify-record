import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import type { LogoutOptions } from '@auth0/auth0-react';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

const serverIp = '109.123.227.242';

export default function Navbar() {
  const { loginWithRedirect, logout, isAuthenticated, user } = useAuth0();

  const handleLogout = () => {
    const options: LogoutOptions = {
      logoutParams: {
        returnTo: `http://${serverIp}:3000/`,
      },
    };
    logout(options);
  };

  return (
    <nav className="navbar navbar-dark bg-dark px-3 justify-content-between">
      <div className="d-flex align-items-center gap-4">
        <span className="navbar-brand mb-0 h1">Logo</span>
        <span className="text-white">Record</span>
        <Link to="/list" className="nav-link text-white">Lists</Link>
        <Link to="/search" className="nav-link text-white">
          <i className="bi bi-search"></i> Search
        </Link>
      </div>

      <div className="dropdown">
        <button
          className="btn btn-light rounded-circle dropdown-toggle"
          type="button"
          id="profileDropdown"
          data-bs-toggle="dropdown"
          aria-expanded="false"
          style={{ width: '40px', height: '40px', padding: 0 }}
        >
          <i className="bi bi-person-fill" style={{ fontSize: '1.5rem' }}></i>
        </button>

        <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="profileDropdown">
          {isAuthenticated ? (
            <>
              <li>{user && <span className="dropdown-item-text">{user.name}</span>}</li>
              <li><Link className="dropdown-item" to="/profile">Profile</Link></li>
              <li><Link className="dropdown-item" to="/settings">Settings</Link></li>
              <li><hr className="dropdown-divider" /></li>
              <li><button className="dropdown-item" onClick={handleLogout}>Logout</button></li>
            </>
          ) : (
            <li><button className="dropdown-item" onClick={() => loginWithRedirect()}>Sign In</button></li>
          )}
        </ul>
      </div>
    </nav>
  );
}
