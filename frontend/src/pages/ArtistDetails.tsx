import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import backgroundImg from '../assets/images/background.jpg';
import { useAuth0 } from "@auth0/auth0-react";


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
  first_played?: string;
  last_played?: string;
}

export default function ArtistDetails() {
  const { artistId } = useParams();
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [artist, setArtist] = useState<ArtistDetailsType | null>(null);
  const [songs, setSongs] = useState<ArtistSong[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchData = async () => {
      try {
        const token = await getAccessTokenSilently();

        const artistRes = await fetch(`/api/artist/${artistId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const artistData = await artistRes.json();
        if ("error" in artistData) {
          setError(artistData.error);
          return;
        }

        // Fetch ALL songs for this artist (remove limit or set to a very high number)
        const songsRes = await fetch(`/api/artist/${artistId}/songs?limit=10000`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const songsData = await songsRes.json();

        let songList: ArtistSong[] = [];

        if (Array.isArray(songsData)) {
          songList = songsData;
        } else if (Array.isArray(songsData.songs)) {
          songList = songsData.songs;
        } else {
          setError("Unexpected format from songs API");
          return;
        }

        setSongs(songList);

        // Determine earliest and latest play timestamps
        const timestamps = songList.flatMap((song) =>
          [song.first_played, song.last_played].filter(Boolean)
        );
        const dates = timestamps.map((ts) => new Date(ts!));
        const firstPlayed = dates.length > 0 ? new Date(Math.min(...dates.map(d => d.getTime()))) : null;
        const lastPlayed = dates.length > 0 ? new Date(Math.max(...dates.map(d => d.getTime()))) : null;

        // Count unique song IDs
        const uniqueSongIds = new Set(songList.map(song => song.song_id));
        const songCount = uniqueSongIds.size;

        setArtist({
          ...artistData,
          first_played: firstPlayed?.toISOString() ?? "",
          last_played: lastPlayed?.toISOString() ?? "",
          song_count: songCount,
        });
      } catch (err: any) {
        setError(err.message || "Failed to fetch artist data");
      }
    };

    fetchData();
  }, [artistId, isAuthenticated, getAccessTokenSilently]);

  if (error) return <p className="text-danger">Error: {error}</p>;
  if (!artist) return <p>Loading...</p>;

  return (
    <div className="container-fluid text-white py-4" style={{minHeight: '100vh', position: 'relative', overflow: 'hidden' }}>
      <img src={backgroundImg} alt="Background" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', objectFit: 'cover', zIndex: 0 }} />

      <div className="container" style={{ position: 'relative', zIndex: 2, maxWidth: '1100px' }}>
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
                    <p><strong>Genres:</strong> {artist.genres?.join(', ')}</p>
                  )}
                  <a href={`https://open.spotify.com/artist/${artist.spotify_uri.split(':')[2]}`} className="btn btn-success w-100">
                    <i className="bi bi-spotify me-2"></i>
                    Open in Spotify
                  </a>
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
                  <p>
                    <strong>First Played:</strong>{" "}
                    {artist.first_played
                      ? new Date(artist.first_played).toLocaleDateString(undefined, {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : "No Date Found"}
                  </p>
                  <p>
                    <strong>Last Played:</strong>{" "}
                    {artist.last_played
                      ? new Date(artist.last_played).toLocaleDateString(undefined, {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : "No Date Found"}
                  </p>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="card bg-dark border-secondary">
                <div className="card-header bg-dark border-secondary">
                  <h3 className="h5 mb-0 text-light">Your Top 10 Songs</h3>
                </div>
                <div className="card-body text-light p-0">
                  {songs.length === 0 ? (
                    <div className="p-3">No songs found.</div>
                  ) : (
                    <table className="table table-dark table-striped table-hover mb-0">
                      <thead>
                        <tr>
                          <th style={{width: '2.5rem'}}>#</th>
                          <th>Song</th>
                          <th>Plays</th>
                        </tr>
                      </thead>
                      <tbody>
                        {songs.slice(0, 10).map((song, idx) => (
                          <tr
                            key={song.song_id}
                            style={{ cursor: "pointer" }}
                            onClick={() => navigate(`/song/${song.song_id}`)}
                          >
                            <td>{idx + 1}</td>
                            <td>{song.track_name}</td>
                            <td>{song.play_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
