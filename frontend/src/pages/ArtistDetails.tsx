import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import 'bootstrap/dist/css/bootstrap.min.css';
import backgroundImg from '../assets/images/background.jpg';

interface ArtistDetailsType {
  artist_id: number;
  name: string;
  spotify_uri: string;
  image_url: string;
  total_streams: number;
  artist_followers?: number;
  artist_popularity?: number;
  artist_genres?: string[];
}

export default function ArtistDetails() {
  const { artistId } = useParams<{ artistId: string }>();
  const [artist, setArtist] = useState<ArtistDetailsType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!artistId) return;

    fetch(`/api/artist/${artistId}`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch artist");
        return res.json();
      })
      .then((data: ArtistDetailsType) => setArtist(data))
      .catch(err => setError(err.message));
  }, [artistId]);

  if (error) return <p className="text-danger p-4">Error: {error}</p>;
  if (!artist) return <p className="p-4">Loading...</p>;

  return (
    <div
      className="container-fluid text-white py-4"
      style={{
        marginTop: '65px',
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
          maxWidth: '900px',
        }}
      >
        <div className="card bg-dark text-white shadow rounded-4 p-4">
          <div className="row mb-4">
            <div className="col-md-auto">
              <div style={{ width: '300px', height: '300px', maxWidth: '100%', position: 'relative' }}>
                <img
                  src={artist.image_url}
                  alt={artist.name}
                  className="img-fluid rounded shadow"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute' }}
                />
              </div>
            </div>
            <div className="col-md-8 d-flex flex-column justify-content-center">
              <h1 className="display-4 mb-0 text-light">{artist.name}</h1>
              {artist.artist_genres && artist.artist_genres.length > 0 && (
                <p className="text-light opacity-75 fst-italic mb-1">
                  {artist.artist_genres.join(", ")}
                </p>
              )}
              <p className="mb-0 text-light opacity-75">
                Followers: {artist.artist_followers?.toLocaleString() ?? 'N/A'}
              </p>
              <p className="mb-0 text-light opacity-75">
                Popularity: {artist.artist_popularity ?? 'N/A'} / 100
              </p>
              <p className="mb-0 text-light opacity-75">
                Total Streams: {artist.total_streams.toLocaleString()}
              </p>
              <a
                href={artist.spotify_uri}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-success mt-3 w-50"
              >
                <i className="bi bi-spotify me-2"></i>
                Open in Spotify
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
