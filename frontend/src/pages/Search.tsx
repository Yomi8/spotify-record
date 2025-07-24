import { useState } from "react";
import { useNavigate } from "react-router-dom";

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
    <div>
      <h1>Search Songs or Artists</h1>
      <form onSubmit={handleSearch}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search for a song or artist"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          Search
        </button>
      </form>
      {loading && <p>Loading...</p>}
      <ul>
        {results.map(song => (
          <li
            key={song.song_id}
            style={{ cursor: "pointer" }}
            onClick={() => navigate(`/song/${song.song_id}`)}
          >
            <img src={song.image_url} alt="" width={40} style={{ verticalAlign: "middle" }} />
            <span style={{ marginLeft: 8 }}>
              {song.track_name} — {song.artist_name}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}