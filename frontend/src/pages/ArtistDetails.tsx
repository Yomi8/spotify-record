import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

type ArtistDetails = {
  artist_id: number;
  name: string;
  spotify_uri: string;
  image_url: string;
  total_streams: number;
};

export default function ArtistDetails() {
  const { artistId } = useParams<{ artistId: string }>();
  const [artist, setArtist] = useState<ArtistDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!artistId) return;

    fetch(`/api/artist/${artistId}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Failed to fetch artist");
        }
        return res.json();
      })
      .then((data) => {
        setArtist(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [artistId]);

  if (loading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;
  if (!artist) return <div className="p-4">Artist not found.</div>;

  return (
    <div className="max-w-xl mx-auto p-4 bg-white bg-opacity-90 rounded-2xl shadow-lg mt-6">
      <h1 className="text-3xl font-bold mb-4">{artist.name}</h1>
      <img
        src={artist.image_url}
        alt={artist.name}
        className="w-64 h-64 object-cover rounded-xl mb-4"
      />
      <p className="text-lg mb-2">
        <strong>Total Streams:</strong> {artist.total_streams.toLocaleString()}
      </p>
      <a
        href={artist.spotify_uri}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block mt-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
      >
        Open in Spotify
      </a>
    </div>
  );
}
