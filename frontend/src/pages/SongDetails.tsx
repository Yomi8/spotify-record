import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

export default function SongDetails() {
  const { songId } = useParams();
  const [song, setSong] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/song/${songId}`)
      .then(res => res.json())
      .then(setSong);
  }, [songId]);

  if (!song) return <p>Loading...</p>;
  if (song.error) return <p>{song.error}</p>;

  return (
    <div>
      <h2>{song.track_name} — {song.artist_name}</h2>
      <img src={song.image_url} alt="" width={120} />
      <ul>
        <li><b>First played:</b> {song.first_played || "N/A"}</li>
        <li><b>Last played:</b> {song.last_played || "N/A"}</li>
        <li><b>Play count:</b> {song.play_count || 0}</li>
        <li><b>Longest binge:</b> {song.longest_binge || 0}</li>
      </ul>
    </div>
  );
}