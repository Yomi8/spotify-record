import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import backgroundImg from '../assets/images/background.jpg';

interface ArtistDetailsType {
  artist_id: number;
  name: string;
  spotify_uri: string;
  image_url: string;
  total_streams: number;
  artist_followers: number;
  artist_popularity: number;
  genres?: string[];
  first_played: string;
  last_played: string;
  song_count: number;
}

interface ArtistSong {
  song_id: number;
  track_name: string;
  play_count: number;
  image_url: string;
}

export default function ArtistDetails() {
  const { artistId } = useParams();
  const [artist, setArtist] = useState<ArtistDetailsType | null>(null);
  const [songs, setSongs] = useState<ArtistSong[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/artist/${artistId}`)
      .then((res) => res.json())
      .then((data) => {
        if ('error' in data) setError(data.error);
        else setArtist(data);
      })
      .catch((err) => setError(err.message));

    fetch(`/api/artist/${artistId}/songs`)
      .then((res) => res.json())
      .then((data) => {
        if ('error' in data) setError(data.error);
        else setSongs(data);
      })
      .catch((err) => setError(err.message));
  }, [artistId]);

  if (error) return <p className="text-danger">Error: {error}</p>;
  if (!artist) return <p>Loading...</p>;

  return (
    <div className="container-fluid text-white py-4" style={{ marginTop: '65px', minHeight: '100vh', position: 'relative', overflow: 'hidden' }}>
      <img src={backgroundImg} alt="Background" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', objectFit: 'cover', zIndex: 0 }} />

      <div className="container" style={{ position: 'relative', zIndex: 2, maxWidth: '1100px' }}>
        <div className="card bg-dark text-white shadow rounded-4 p-4">
          <div className="row mb-4">
            <div className="col-md-auto">
              <div style={{ width: '300px', height: '300px', maxWidth: '100%', position: 'relative' }}>
                <img
                  src={artist.image_url}
                  alt={`${artist.name}`}
                  className="img-fluid rounded shadow"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute' }}
                />
              </div>
            </div>
            <div className="col-md-8 d-flex flex-column justify-content-center">
              <h1 className="display-4 mb-0 text-light">{artist.name}</h1>
            </div>
          </div>

          <div className="row">
            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Artist Info</h3>
                </div>
                <div className="card-body text-light">
                  <p><strong>Followers:</strong> {artist.artist_followers.toLocaleString()}</p>
                  <p><strong>Popularity:</strong> {artist.artist_popularity}</p>
                  {artist.genres && artist.genres.length > 0 && (
                    <p><strong>Genres:</strong> {artist.genres.join(', ')}</p>
                  )}
                  <a href={`https://open.spotify.com/artist/${artist.spotify_uri.split(':')[2]}`} target="_blank" rel="noreferrer" className="btn btn-success mt-2">Open in Spotify</a>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Listening Stats</h3>
                </div>
                <div className="card-body text-light">
                  <p><strong>Total Streams:</strong> {artist.total_streams.toLocaleString()}</p>
                  <p><strong>Songs Played:</strong> {artist.song_count}</p>
                  <p><strong>First Played:</strong> {new Date(artist.first_played).toLocaleDateString()}</p>
                  <p><strong>Last Played:</strong> {new Date(artist.last_played).toLocaleDateString()}</p>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Top Songs</h3>
                </div>
                <div className="card-body text-light">
                  <ul className="list-group list-group-flush">
                    {songs.map((song) => (
                      <li key={song.song_id} className="list-group-item bg-dark text-light d-flex justify-content-between align-items-center">
                        <span>{song.track_name}</span>
                        <span className="badge bg-success">{song.play_count}</span>
                      </li>
                    ))}
                    {songs.length === 0 && <li className="list-group-item bg-dark text-light">No songs found.</li>}
                  </ul>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}