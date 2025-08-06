import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

export default function ArtistDetail() {
  const { artistId } = useParams();
  const [artist, setArtist] = useState(null);

  useEffect(() => {
    fetch(`/api/artists/${artistId}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    })
      .then(res => res.json())
      .then(data => setArtist(data));
  }, [artistId]);

  if (!artist) return <p>Loading...</p>;

  return (
    <div className="max-w-xl mx-auto p-4 bg-white/80 rounded-xl shadow-lg">
      <h1 className="text-2xl font-bold">{artist.name}</h1>
      {artist.image_url && <img src={artist.image_url} alt={artist.name} className="rounded my-4" />}
      <p>Total Streams: {artist.total_streams}</p>
      <a href={`https://open.spotify.com/artist/${artist.spotify_uri}`} target="_blank" rel="noreferrer">
        View on Spotify
      </a>
    </div>
  );
}
