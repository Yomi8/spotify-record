import { useState } from "react";
import { useNavigate } from "react-router-dom";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import backgroundImg from '../assets/images/background.jpg';

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    setResults(data.results || []);
    setLoading(false);
  };

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

      {/* Main content */}
      <div
        className="container"
        style={{
          marginTop: '65px',
          position: 'relative',
          zIndex: 2,
          maxWidth: '900px',
        }}
      >
        <div className="card bg-dark text-white shadow rounded-4 p-4">
          <h1 className="display-4 text-center mb-2">Search</h1>
          <p className="text-center text-light-50 mb-4">Click on a result to view more details</p>

          <form onSubmit={handleSearch} className="mb-5">
            <div className="input-group position-relative" style={{ padding: '10px' }}>
              <input
                className="form-control form-control-lg bg-white text-dark border-0 rounded-pill"
                style={{
                  paddingLeft: '25px',
                  paddingRight: '60px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                }}
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search for a song or artist"
              />
              <button
                className="btn rounded-circle"
                type="submit"
                disabled={loading || !query.trim()}
                style={{
                  position: 'absolute',
                  right: '20px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 10,
                  width: '40px',
                  height: '40px',
                  backgroundColor: '#1a1a1a',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: 'none',
                }}
              >
                {loading ? (
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                ) : (
                  <i className="bi bi-search"></i>
                )}
              </button>
            </div>
          </form>

          {loading && (
            <div className="text-center mb-4">
              <div className="spinner-border text-light" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          )}

          <div className="list-group">
            {results.map(song => (
              <div
                key={song.song_id}
                className="list-group-item list-group-item-action bg-dark text-light border-secondary d-flex align-items-center"
                onClick={() => navigate(`/song/${song.song_id}`)}
                style={{ cursor: "pointer" }}
              >
                <img
                  src={song.image_url}
                  alt=""
                  className="me-3"
                  width={50}
                  height={50}
                  style={{ objectFit: "cover" }}
                />
                <div>
                  <h6 className="mb-0">{song.track_name}</h6>
                  <small className="text-light-50">{song.artist_name}</small>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
