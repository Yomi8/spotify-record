import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

export default function Navbar() {
  return (
    <nav className="navbar navbar-dark bg-dark px-3">
      {/* Left group: logo + nav items */}
      <div className="d-flex align-items-center gap-4">
        <span className="navbar-brand mb-0 h1">Logo</span>
        <span className="text-white">Record</span>
        <Link to="/list" className="nav-link text-white">Lists</Link>
        <Link to="/search" className="nav-link text-white">
          <i className="bi bi-search"></i> Search
        </Link>
      </div>

      {/* Right: profile icon */}
      <div 
        className="rounded-circle bg-light d-flex justify-content-center align-items-center"
        style={{ width: '30px', height: '30px' }}
      >
        <i className="bi bi-person" style={{ color: '#222' }}></i>
      </div>
    </nav>
  );
}