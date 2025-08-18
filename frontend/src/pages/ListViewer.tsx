import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import backgroundImg from "../assets/images/background.jpg";
import { useAuth0 } from "@auth0/auth0-react";
import dayjs from "dayjs";
import { Link } from "react-router-dom";

type Song = {
  song_id: string;
  track_name: string;
  artist_id: string;
  artist_name: string;
  image_url?: string;
  play_count: number;
};

type Artist = {
  artist_name: string;
  artist_id: string;
  image_url?: string;
  play_count: number;
};

export default function ListViewer() {
  const { listType } = useParams();
  const { getAccessTokenSilently, isAuthenticated, isLoading: authLoading } = useAuth0();

  const [songs, setSongs] = useState<Song[]>([]);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(false);

  // Custom list state
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [customLimit, setCustomLimit] = useState(10);
  const [customType, setCustomType] = useState<"songs" | "artists">("songs");

  const listOptions = [
    { label: "Top 100 Songs", type: "top-100-songs", isSongList: true, isArtistList: false, limit: 100 },
    { label: "Your Top Artists", type: "top-artists", isSongList: false, isArtistList: true, limit: 100 },
    { label: "Top Songs of All Time", type: "top-songs-all-time", isSongList: true, isArtistList: false, limit: 100 },
    { label: "Top 10 Artists", type: "top-10-artists", isSongList: false, isArtistList: true, limit: 10 },
    { label: "Top 10 Songs This Year", type: "top-10-this-year", isSongList: true, isArtistList: false, limit: 10 },
    { label: "Create Custom List", type: "custom", isSongList: false, isArtistList: false, limit: 0 },
  ];

  const currentOption = listOptions.find(opt => opt.type === listType);
  const isSongList = currentOption?.isSongList ?? false;
  const isArtistList = currentOption?.isArtistList ?? false;
  const limit = currentOption?.limit ?? 100;
  const listLabel = currentOption?.label ?? "List not found";

  let start: string | undefined;
  let end: string | undefined;
  if (listType === "top-10-this-year") {
    end = dayjs().toISOString();
    start = dayjs().subtract(1, "year").toISOString();
  }

  useEffect(() => {
    if (!isAuthenticated || listType === "custom") return; // skip for custom
    const fetchData = async () => {
      console.log("Fetching prebuilt list:", listType);
      setLoading(true);
      try {
        const token = await getAccessTokenSilently();
        const endpoint = isSongList ? "/api/lists/songs" : "/api/lists/artists";
        const res = await axios.get(endpoint, {
          params: { start, end, limit },
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });
        if (isSongList) setSongs(res.data.songs);
        else setArtists(res.data.artists);
      } catch (err) {
        console.error("Error fetching prebuilt list", err);
        setSongs([]);
        setArtists([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [listType, isAuthenticated]);

  const fetchCustomList = async () => {
    console.log("Custom list button clicked");
    if (!isAuthenticated) {
      console.warn("Not authenticated, cannot fetch");
      return;
    }
    setLoading(true);
    try {
      const token = await getAccessTokenSilently();
      console.log("Got token, fetching custom list:", customType, customStart, customEnd, customLimit);
      const endpoint = customType === "songs" ? "/api/lists/songs" : "/api/lists/artists";
      const res = await axios.get(endpoint, {
        params: {
          start: customStart || undefined,
          end: customEnd || undefined,
          limit: customLimit || undefined,
        },
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      if (customType === "songs") {
        setSongs(res.data.songs);
        setArtists([]);
      } else {
        setArtists(res.data.artists);
        setSongs([]);
      }
    } catch (err) {
      console.error("Error fetching custom list", err);
      setSongs([]);
      setArtists([]);
    } finally {
      setLoading(false);
    }
  };

  const renderSongsTable = (songsList: Song[]) => (
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
        {songsList.map((song, idx) => (
          <tr key={song.song_id}>
            <td>{idx + 1}</td>
            <td>
              <Link to={`/song/${song.song_id}`} className="text-white text-decoration-none">
                {song.track_name}
              </Link>
            </td>
            <td>
              <Link to={`/artist/${song.artist_id}`} className="text-white text-decoration-none">
                {song.artist_name}
              </Link>
            </td>
            <td>{song.play_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderArtistsTable = (artistsList: Artist[]) => (
    <table className="table table-dark table-striped">
      <thead>
        <tr>
          <th>#</th>
          <th>Artist</th>
          <th>Plays</th>
        </tr>
      </thead>
      <tbody>
        {artistsList.map((artist, idx) => (
          <tr key={artist.artist_name}>
            <td>{idx + 1}</td>
            <td>
              <Link to={`/artist/${artist.artist_id}`} className="text-white text-decoration-none">
                {artist.artist_name}
              </Link>
            </td>
            <td>{artist.play_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    if (listType === "custom") {
      return (
        <div>
          <h2>Custom List Builder</h2>

          <div className="mb-3">
            <label className="form-label">List Type</label>
            <select
              className="form-select"
              value={customType}
              onChange={(e) => setCustomType(e.target.value as "songs" | "artists")}
            >
              <option value="songs">Songs</option>
              <option value="artists">Artists</option>
            </select>
          </div>

          <div className="mb-3">
            <label className="form-label">Start Date</label>
            <input
              type="date"
              className="form-control"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label className="form-label">End Date</label>
            <input
              type="date"
              className="form-control"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Limit</label>
            <input
              type="number"
              className="form-control"
              value={customLimit}
              onChange={(e) => setCustomLimit(Number(e.target.value))}
            />
          </div>

          <button className="btn btn-primary mb-4" onClick={fetchCustomList}>
            Generate List
          </button>

          {songs.length > 0 && renderSongsTable(songs)}
          {artists.length > 0 && renderArtistsTable(artists)}
        </div>
      );
    }

    if (isSongList) return renderSongsTable(songs);
    if (isArtistList) return renderArtistsTable(artists);
    return <h2>List not found</h2>;
  };

  if (authLoading) return <div>Loading authentication...</div>;
  if (!isAuthenticated) return <div>Please log in to view lists.</div>;

  return (
    <div
      className="container-fluid text-white py-4"
      style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}
    >
      <img
        src={backgroundImg}
        alt="Abstract Background"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          objectFit: "cover",
          zIndex: 0,
        }}
      />
      <div
        className="card bg-dark text-white shadow rounded-4"
        style={{
          position: "relative",
          zIndex: 1,
          width: "fit-content",
          minWidth: "300px",
          margin: "auto auto 0 auto",
          padding: "2rem",
        }}
      >
        <div className="max-w-4xl px-4">
          <h1 className="text-2xl font-bold mb-6 text-center capitalize">{listLabel}</h1>
          <div className="p-4 border rounded-lg shadow">{renderContent()}</div>
        </div>
      </div>
    </div>
  );
}
