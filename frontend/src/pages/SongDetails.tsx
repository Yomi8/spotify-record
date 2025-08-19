import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import 'bootstrap/dist/css/bootstrap.min.css';
import backgroundImg from '../assets/images/background.jpg';
import { Link } from 'react-router-dom';

interface SongDetails {
  song_id: number;
  spotify_uri: string;
  track_name: string;
  artist_name: string;
  artist_id: string;
  album_name: string;
  album_id: string;
  album_type: string;
  album_uri: string;
  release_date: string;
  release_date_precision: string;
  duration_ms: number;
  is_explicit: boolean;
  image_url: string;
  preview_url: string;
  popularity: number;
  is_local: boolean;
  created_at: string;
  first_played: string;
  last_played: string;
  play_count: number;
  days_played: number;
  longest_binge: number;
}

interface ErrorResponse {
  error: string;
}

export default function SongDetails() {
  const { songId } = useParams();
  const [song, setSong] = useState<SongDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`/api/song/${songId}`)
      .then(res => res.json())
      .then((data: SongDetails | ErrorResponse) => {
        if ('error' in data) {
          setError(data.error);
        } else {
          setSong(data as SongDetails);
        }
      })
      .catch(err => setError(err.message));
  }, [songId]);

  if (error) return <p className="text-danger">Error: {error}</p>;
  if (!song) return <p>Loading...</p>;

  const duration = `${Math.floor(song.duration_ms / 60000)}:${(
    (song.duration_ms % 60000) / 1000
  ).toFixed(0).padStart(2, '0')}`;

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

      {/* Content container */}
      <div
        className="container"
        style={{
          position: 'relative',
          zIndex: 2,
          maxWidth: '1100px',
        }}
      >
        <div className="card bg-dark text-white shadow rounded-4 p-4" style={{ position: 'relative' }}>
          {/* Back button above card content */}
          <button
            className="btn btn-outline-light mb-3"
            style={{ width: "80px", display: "block", textAlign: "left" }}
            onClick={() => navigate(-1)}
          >
            <i className="bi bi-arrow-left"></i> Back
          </button>

          <div className="row mb-4">
            <div className="col-md-auto">
              <div style={{ width: '300px', height: '300px', maxWidth: '100%', position: 'relative' }}>
                <img
                  src={song.image_url}
                  alt={`${song.track_name} album art`}
                  className="img-fluid rounded shadow"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute' }}
                />
              </div>
            </div>
            <div className="col-md-8 d-flex flex-column justify-content-center">
              <h1 className="display-4 mb-0 text-light">{song.track_name}</h1>
              <Link to={`/artist/${song.artist_id}`} className="text-decoration-none text-light">
                <h2 className="h3 text-light opacity-75">{song.artist_name}</h2>
              </Link>
            </div>
          </div>

          <div className="row">
            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Album Information</h3>
                </div>
                <div className="card-body text-light">
                  <dl className="row mb-0">
                    <dt className="col-sm-4 text-light opacity-75">Album</dt>
                    <dd className="col-sm-8">{song.album_name}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Type</dt>
                    <dd className="col-sm-8">{song.album_type}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Released</dt>
                    <dd className="col-sm-8">{song.release_date}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Duration</dt>
                    <dd className="col-sm-8">{duration}</dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Track Details</h3>
                </div>
                <div className="card-body text-light">
                  <dl className="row mb-0">
                    <dt className="col-sm-4 text-light opacity-75">Explicit</dt>
                    <dd className="col-sm-8">{song.is_explicit ? 'Yes' : 'No'}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Popularity</dt>
                    <dd className="col-sm-8">
                      <div className="progress bg-dark">
                        <div className="progress-bar bg-success" style={{ width: `${song.popularity}%` }}>
                          {song.popularity}%
                        </div>
                      </div>
                    </dd>
                    <dt className="col-sm-4 text-light opacity-75">Local Track</dt>
                    <dd className="col-sm-8">{song.is_local ? 'Yes' : 'No'}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Added</dt>
                    <dd className="col-sm-8">{new Date(song.created_at).toLocaleDateString()}</dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Listening Statistics</h3>
                </div>
                <div className="card-body text-light">
                  <dl className="row mb-0">
                    <dt className="col-sm-4 text-light opacity-75">First Play</dt>
                    <dd className="col-sm-8">{new Date(song.first_played).toLocaleDateString()}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Last Play</dt>
                    <dd className="col-sm-8">{new Date(song.last_played).toLocaleDateString()}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Total Plays</dt>
                    <dd className="col-sm-8">{song.play_count}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Days Played</dt>
                    <dd className="col-sm-8">{song.days_played}</dd>
                    <dt className="col-sm-4 text-light opacity-75">Longest Binge</dt>
                    <dd className="col-sm-8">{song.longest_binge} plays</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="row mt-4">
            <div className="col-12">
              <div className="card bg-dark border-secondary">
                <div className="card-body">
                  {song.preview_url && (
                    <div className="mb-3">
                      <audio controls className="w-100">
                        <source src={song.preview_url} type="audio/mpeg" />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  )}
                  <a href={`spotify:track:${song.spotify_uri}`} className="btn btn-success w-100">
                    <i className="bi bi-spotify me-2"></i>
                    Open in Spotify
                  </a>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
