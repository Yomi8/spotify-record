import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

export default function Footer() {
  return (
    <footer
      className="navbar navbar-dark bg-black px-3 justify-content-between"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 10,
      }}
    >
      <div className="d-flex align-items-center gap-4">
        <Link to="/acknoledgements" className="nav-link text-white">
          <i className="bi bi-paperclip"></i> Acknowledgements
        </Link>
        <Link to="/help" className="nav-link text-white">
          <i className="bi bi-patch-question"></i> Help
        </Link>
      </div>
      <div className="text-white small">
        © {new Date().getFullYear()} Record
      </div>
    </footer>
  );
}