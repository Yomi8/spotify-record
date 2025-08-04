import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import backgroundImg from "../assets/images/background.jpg";

type Song = {
  song_id: string;
  track_name: string;
  artist_name: string;
  image_url?: string;
  play_count: number;
};

type Artist = {
  artist_name: string;
  image_url?: string;
  play_count: number;
};

export default function ListViewer() {
  const { listType } = useParams();
  const [songs, setSongs] = useState<Song[]>([]);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(false);

  // Example: You can set these based on user input or listType
  const start = undefined; // e.g. "2025-08-01"
  const end = undefined;   // e.g. "2025-08-04"
  const limit = listType === "top-10-this-week" || listType === "top-10-artists" ? 10 : 100;

  useEffect(() => {
    setLoading(true);
    if (
      listType === "top-100-songs" ||
      listType === "top-songs-all-time" ||
      listType === "top-10-this-week"
    ) {
      axios
        .get("/api/lists/top-songs", {
          params: { start, end, limit },
          withCredentials: true,
        })
        .then((res: { data: { songs: Song[] } }) => setSongs(res.data.songs))
        .catch(() => setSongs([]))
        .finally(() => setLoading(false));
    } else if (
      listType === "top-artists" ||
      listType === "top-10-artists"
    ) {
      axios
        .get("/api/lists/top-artists", {
          params: { start, end, limit },
          withCredentials: true,
        })
        .then((res: { data: { artists: Artist[] } }) => setArtists(res.data.artists))
        .catch(() => setArtists([]))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [listType, start, end, limit]);

  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    switch (listType) {
      case "top-100-songs":
      case "top-songs-all-time":
      case "top-10-this-week":
        return (
          <table className="table table-dark table-striped">
            <thead>
              <tr>
                <th>#</th>
                <th>Song</th>
                <th>Artist</th>
                <th>Plays</th>
              </tr>
            </thead>
            <tbody>
              {songs.map((song, idx) => (
                <tr key={song.song_id}>
                  <td>{idx + 1}</td>
                  <td>{song.track_name}</td>
                  <td>{song.artist_name}</td>
                  <td>{song.play_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        );
      case "top-artists":
      case "top-10-artists":
        return (
          <table className="table table-dark table-striped">
            <thead>
              <tr>
                <th>#</th>
                <th>Artist</th>
                <th>Plays</th>
              </tr>
            </thead>
            <tbody>
              {artists.map((artist, idx) => (
                <tr key={artist.artist_name}>
                  <td>{idx + 1}</td>
                  <td>{artist.artist_name}</td>
                  <td>{artist.play_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        );
      case "custom":
        return <h2>Custom List Builder</h2>;
      default:
        return <h2>List not found</h2>;
    }
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
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                objectFit: 'cover',
                zIndex: 0,
              }}
            />

            {/* Main content */}
            <div className="card bg-dark text-white shadow rounded-4 p-4" style={{marginTop:'65px', position: 'relative', zIndex: 1 }}>
                <div className="max-w-4xl mx-auto mt-10 px-4">
                  <h1 className="text-2xl font-bold mb-6 text-center capitalize">
                    {listType?.replaceAll("-", " ")}
                  </h1>
                  <div className="p-4 border rounded-lg shadow">{renderContent()}</div>
                </div>
            </div>
        </div>
  );
}
