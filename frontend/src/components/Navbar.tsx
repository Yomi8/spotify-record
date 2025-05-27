import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

export default function Navbar() {
  return (
    <nav className="navbar navbar-dark bg-dark px-3">
      {/* Logo and static brand label */}
      <div className="d-flex align-items-center gap-3">
        <span className="navbar-brand mb-0 h1">Logo</span>
        <span className="text-white">Record</span>
      </div>

      {/* Navigation links and user icon */}
      <div className="d-flex align-items-center gap-4">
        <Link to="/list" className="nav-link text-white">Lists</Link>
        <Link to="/search" className="nav-link text-white">
          <i className="bi bi-search"></i> Search
        </Link>

        {/* Profile circle placeholder */}
        <div 
          className="rounded-circle bg-light d-flex justify-content-center align-items-center"
          style={{ width: '30px', height: '30px' }}
        >
          <i className="bi bi-person" style={{ color: '#222' }}></i>
        </div>
      </div>
    </nav>
  );
}