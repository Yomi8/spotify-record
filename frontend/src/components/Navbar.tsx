import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

export default function Navbar() {
  return (
    <nav className="navbar navbar-dark bg-dark px-3 justify-content-between">
      {/* Left side */}
      <div className="d-flex align-items-center gap-4">
        <span className="navbar-brand mb-0 h1">Logo</span>
        <span className="text-white">Record</span>
        <Link to="/list" className="nav-link text-white">Lists</Link>
        <Link to="/search" className="nav-link text-white">
          <i className="bi bi-search"></i> Search
        </Link>
      </div>

      {/* Right side: Profile Dropdown */}
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
          <li><Link className="dropdown-item" to="/profile">Profile</Link></li>
          <li><Link className="dropdown-item" to="/settings">Settings</Link></li>
          <li><hr className="dropdown-divider" /></li>
          <li><button className="dropdown-item">Logout</button></li>
        </ul>
      </div>
    </nav>
  );
}