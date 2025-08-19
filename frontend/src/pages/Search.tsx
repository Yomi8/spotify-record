import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import backgroundImg from '../assets/images/background.jpg';

export default function Search() {
  const navigate = useNavigate();
  const location = useLocation();

  // Read query param from URL
  const params = new URLSearchParams(location.search);
  const initialQuery = params.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [songResults, setSongResults] = useState<any[]>([]);
  const [artistResults, setArtistResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Auto-search if query param is present
  useEffect(() => {
    if (initialQuery) {
      handleSearch(undefined, initialQuery);
    }
    // eslint-disable-next-line
  }, [initialQuery]);

  // Modified handleSearch to accept optional query
  const handleSearch = async (
    e?: React.FormEvent,
    q?: string
  ) => {
    if (e) e.preventDefault();
    const searchTerm = typeof q === "string" ? q : query;
    if (!searchTerm.trim()) return;
    setLoading(true);
    // Update URL
    navigate(`/search?q=${encodeURIComponent(searchTerm)}`, { replace: true });
    const res = await fetch(`/api/search?q=${encodeURIComponent(searchTerm)}`);
    const data = await res.json();
    setSongResults(data.songs || []);
    setArtistResults(data.artists || []);
    setLoading(false);
  };

  return (
    <div
      className="container-fluid text-white py-4"
      style={{
        minHeight: '100vh',
        position: 'relative',
        overflow: 'visible'
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

      <div style={{ position: "relative", zIndex: 2, marginTop: "-33px" }}>
        <div className="row justify-content-center">
          <div className="col-md-8">
            
            {/* Header card */}
            <div
              className="card bg-dark text-white shadow mx-0 mb-4"
              style={{
                borderTopLeftRadius: 0,
                borderTopRightRadius: 0,
                borderBottomLeftRadius: ".5rem",
                borderBottomRightRadius: ".5rem",
                maxWidth: "fit-content",
              }}
            >
              <div className="card-body py-3 px-4">
                <h1 className="mb-0">Search</h1>
              </div>
            </div>

            {/* Search form card */}
            <div className="card bg-dark text-white shadow p-4 mb-4">
              {/* Back button inside the card, above content */}
              <button
                className="btn btn-outline-light mb-3"
                style={{
                  width: "85px",
                  textAlign: "left",
                  position: "absolute",
                  marginLeft: 0,
                }}
                onClick={() => navigate(-1)}
              >
                <i className="bi bi-arrow-left"></i> Back
              </button>
              <p className="text-center text-light-50 my-3">Click on a result to view more details</p>

              <form onSubmit={handleSearch}>
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
                <div className="text-center mt-4">
                  <div className="spinner-border text-light" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Results card */}
            {(artistResults.length > 0 || songResults.length > 0) && (
              <div className="card bg-dark text-white shadow p-4">
                {/* ARTIST RESULTS */}
                {artistResults.length > 0 && (
                  <>
                    <h4 className="mb-3">Artists</h4>
                    <div className="list-group mb-4">
                      {artistResults.map(artist => (
                        <div
                          key={artist.artist_id}
                          className="list-group-item list-group-item-action bg-dark text-light border-secondary d-flex align-items-center"
                          onClick={() => navigate(`/artist/${artist.artist_id}`)}
                          style={{ cursor: "pointer" }}
                        >
                          <img
                            src={artist.image_url}
                            alt=""
                            className="me-3"
                            width={50}
                            height={50}
                            style={{ objectFit: "cover" }}
                          />
                          <div>
                            <h6 className="mb-0">{artist.artist_name}</h6>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {/* SONG RESULTS */}
                {songResults.length > 0 && (
                  <>
                    <h4 className="mb-3">Songs</h4>
                    <div className="list-group">
                      {songResults.map(song => (
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
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
