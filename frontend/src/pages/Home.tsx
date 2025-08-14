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
      style={{ minHeight: '100vh', position: 'relative', overflow: 'visible' }}
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

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 2, marginTop: '-33px' }}>
        <div className="row justify-content-center">
          <div className="col-md-8">
            {/* Header card */}
            <div
              className="card bg-dark text-white shadow mx-0 mb-4"
              style={{
                borderTopLeftRadius: 0,
                borderTopRightRadius: 0,
                borderBottomLeftRadius: '.5rem',
                borderBottomRightRadius: '.5rem',
                maxWidth: 'fit-content',
              }}
            >
              <div className="card-body py-3 px-4">
                <h1 className="mb-0">
                  Welcome, {isAuthenticated
                    ? user?.nickname || user?.name || user?.email || 'User'
                    : 'Guest'}
                </h1>
              </div>
            </div>

            {/* Stats card */}
            <div className="card bg-dark text-white shadow p-4">
              <div className="d-flex align-items-center mb-4">
                <i className="bi bi-graph-up me-2"></i>
                <h4 className="mb-0">Your Top Charts</h4>
              </div>

              {!isAuthenticated && (
                <div className="alert alert-info">
                  Please log in to view your stats.
                </div>
              )}

              {isAuthenticated && loading && (
                <div className="text-center p-4">
                  <div className="spinner-border text-light mb-2" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mb-0">Loading your stats... (attempt {retryCount + 1}/10)</p>
                </div>
              )}

              {isAuthenticated && error && (
                <div className="alert alert-danger">
                  {error}
                </div>
              )}

              {isAuthenticated && !stats && retryCount >= 10 && (
                <div className="alert alert-warning">
                  Snapshot took too long to generate. Please try again later.
                </div>
              )}

              {isAuthenticated && stats && (
                <div className="row g-4">
                  {/* Most Played Section */}
                  <div className="col-md-6">
                    <div className="card bg-secondary">
                      <div className="card-body">
                        <h5 className="card-title mb-3">Most Played</h5>
                        <div className="d-flex align-items-center mb-3">
                          {stats.most_played_song_image_url && (
                            <img 
                              src={stats.most_played_song_image_url} 
                              alt="Top Song" 
                              className="rounded me-3"
                              style={{width: 64, height: 64}} 
                            />
                          )}
                          <div>
                            <p className="fw-bold mb-1">Song: {stats.most_played_song}</p>
                            <p className="mb-0">Artist: {stats.most_played_artist}</p>
                            <small className="text-light-50">Total Plays: {stats.total_plays}</small>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Longest Binge Section */}
                  <div className="col-md-6">
                    <div className="card bg-secondary">
                      <div className="card-body">
                        <h5 className="card-title mb-3">Longest Binge</h5>
                        <div className="d-flex align-items-center mb-3">
                          {stats.longest_binge_song_image_url && (
                            <img 
                              src={stats.longest_binge_song_image_url} 
                              alt="Binge Song" 
                              className="rounded me-3"
                              style={{width: 64, height: 64}} 
                            />
                          )}
                          <div>
                            <p className="fw-bold mb-1">Song: {stats.longest_binge_song}</p>
                            <p className="mb-0">Artist: {stats.longest_binge_artist}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}