import 'bootstrap/dist/css/bootstrap.min.css';
import { useAuth0 } from '@auth0/auth0-react';
import { useEffect, useState } from 'react';
import backgroundImg from '../assets/images/background.jpg';

export default function Home() {
  const { user, isAuthenticated, getAccessTokenSilently } = useAuth0();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSnapshot = async (retryCount = 0) => {
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch('/api/snapshots/lifetime/latest', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 200) {
        const data = await response.json();
        setStats(data.snapshot);
        setLoading(false);
      } else if (response.status === 202 && retryCount < 10) {
        // Job started, wait and retry
        setTimeout(() => fetchSnapshot(retryCount + 1), 3000); // Retry after 3 sec
      } else {
        throw new Error('Snapshot not ready or too many retries');
      }
    } catch (err) {
      console.error(err);
      setError('Could not load stats.');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      setLoading(true);
      fetchSnapshot();
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  return (
    <div
      className="container-fluid text-white py-4"
      style={{ minHeight: '100vh', background: 'linear-gradient(to right, #000, #333)' }}
    >
      <h1>
        Welcome{' '}
        <span>
          {isAuthenticated
            ? user?.nickname || user?.name || user?.email || 'User'
            : 'Guest'}
        </span>
        !
      </h1>

      <div className="row mt-4">
        {/* Left card */}
        <div className="col-md-6">
          <div className="card bg-dark text-white shadow">
            <div className="card-header">
              <i className="bi bi-bar-chart me-2"></i> Quick Bits
            </div>
            <div className="card-body">
              {!isAuthenticated && (
                <p>Please log in to view your stats.</p>
              )}

              {isAuthenticated && loading && (
                <p>Loading your stats...</p>
              )}

              {isAuthenticated && error && (
                <p className="text-danger">{error}</p>
              )}

              {isAuthenticated && stats && (
                <div>
                  <p><strong>Total Songs Played:</strong> {stats.total_songs}</p>
                  <p><strong>Top Artist:</strong> {stats.top_artist}</p>
                  <p><strong>Top Genre:</strong> {stats.top_genre}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right image */}
        <div className="col-md-6 position-relative p-0">
          <img
            src={backgroundImg}
            alt="Abstract Background"
            style={{
              width: '100%',
              height: '100vh',
              objectFit: 'cover',
              display: 'block',
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '40%',
              height: '100%',
              background: 'linear-gradient(to right, rgba(0,0,0,1), rgba(0,0,0,0))',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>
    </div>
  );
}