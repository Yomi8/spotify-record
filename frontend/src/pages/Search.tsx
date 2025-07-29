import { useState } from "react";
import { useNavigate } from "react-router-dom";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

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
    <div className="container-fluid min-vh-100 bg-dark text-light">
      <div className="row justify-content-center text-center pt-5">
        <div className="col-md-8">
          <h1 className="display-4 mb-2">[Your Main Text Here]</h1>
          <p className="text-light-50 mb-4">[Your Secondary Text Here]</p>
          
          <form onSubmit={handleSearch} className="mb-5">
            <div className="input-group position-relative" style={{ padding: '10px' }}>
              <input
                className="form-control form-control-lg bg-white text-dark border-0 rounded-pill"
                style={{
                  paddingLeft: '25px',
                  paddingRight: '60px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
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
                  border: 'none'
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
        </div>
      </div>

      {loading && (
        <div className="text-center">
          <div className="spinner-border text-light" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      )}

      <div className="row justify-content-center">
        <div className="col-md-8">
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