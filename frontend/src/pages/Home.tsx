import 'bootstrap/dist/css/bootstrap.min.css';
import { useAuth0 } from '@auth0/auth0-react';
import { useEffect, useState } from 'react';
import backgroundImg from '../assets/images/background.jpg';

export default function Home() {
  const { user, isAuthenticated, getAccessTokenSilently } = useAuth0();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchSnapshot = async (retry = 0) => {
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch('/api/snapshots/lifetime/latest', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log(`Snapshot fetch attempt ${retry}, status: ${response.status}`);

      if (response.status === 200) {
        const data = await response.json();
        setStats(data.snapshot);
        setLoading(false);
        setRetryCount(0);
      } else if (response.status === 202 && retry < 10) {
        setRetryCount(retry + 1);
        setTimeout(() => fetchSnapshot(retry + 1), 3000);
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
      setError(null);
      setStats(null);
      fetchSnapshot();
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  return (
    <div
      className="container-fluid text-white py-4"
      style={{
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background image */}
      <img
        src={backgroundImg}
        alt="Abstract Background"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
        }}
      />
      {/* Gradient overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'linear-gradient(to right, #000 60%, #333 100%)',
          opacity: 0.85,
          zIndex: 1,
          pointerEvents: 'none',
        }}
      />

      {/* Main content */}
      <div style={{position: 'relative', zIndex: 2 }}>
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
                  <p>Loading your stats... (attempt {retryCount + 1}/10)</p>
                )}

                {isAuthenticated && error && (
                  <p className="text-danger">{error}</p>
                )}

                {isAuthenticated && !stats && retryCount >= 10 && (
                  <p className="text-warning">
                    Snapshot took too long to generate. Please try again later.
                  </p>
                )}

                {isAuthenticated && stats && (
                  <div>
                    <p><strong>Total Plays:</strong> {stats.total_plays}</p>
                    <p><strong>Top Song:</strong> {stats.most_played_song}</p>
                    <p><strong>Top Artist:</strong> {stats.most_played_artist}</p>
                    {stats.most_played_song_image_url && (
                      <img src={stats.most_played_song_image_url} alt="Top Song Cover" style={{width: 64, height: 64}} />
                    )}

                    <p><strong>Longest Binge Song:</strong> {stats.longest_binge_song}</p>
                    <p><strong>Binge Artist:</strong> {stats.longest_binge_artist}</p>
                    {stats.longest_binge_song_image_url && (
                      <img src={stats.longest_binge_song_image_url} alt="Binge Song Cover" style={{width: 64, height: 64}} />
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}