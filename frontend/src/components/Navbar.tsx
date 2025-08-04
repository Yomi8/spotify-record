import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

export default function Navbar() {
  const { loginWithRedirect, logout, isAuthenticated, user, getAccessTokenSilently } = useAuth0();

  const handleConnectSpotify = async () => {
    const token = await getAccessTokenSilently();
    window.location.href = `https://yomi16.nz/api/spotify/login?access_token=${token}`;
  };

  const handleFetchRecent = async () => {
    const token = await getAccessTokenSilently();
    try {
      const res = await fetch('https://yomi16.nz/api/spotify/fetch-recent', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      const data = await res.json();
      console.log(data);
      alert('Recent tracks fetch initiated.');
    } catch (err) {
      alert('Error fetching recent tracks.');
      console.error(err);
    }
  };

  return (
    <nav className="navbar navbar-dark bg-black px-3 justify-content-between"
    style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 10,
     }}    
    >
      <div className="d-flex align-items-center gap-4">
        <div>
          <span className="navbar-brand mb-0 h1">Logo</span>
          <Link to="/" className="text-white">Record</Link>
        </div>
        <Link to="/lists" className="nav-link text-white">Lists</Link>
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

              <li>
                <button className="dropdown-item" onClick={handleConnectSpotify}>
                  Connect to Spotify
                </button>
              </li>
              <li>
                <button className="dropdown-item" onClick={handleFetchRecent}>
                  Fetch Recent Tracks
                </button>
              </li>

              <li><hr className="dropdown-divider" /></li>
              <li>
                <button className="dropdown-item" onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}>
                  Logout
                </button>
              </li>
            </>
          ) : (
            <li><button className="dropdown-item" onClick={() => loginWithRedirect()}>Sign In</button></li>
          )}
        </ul>
      </div>
    </nav>
  );
}
