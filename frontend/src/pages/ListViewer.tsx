import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import backgroundImg from "../assets/images/background.jpg";
import { useAuth0 } from "@auth0/auth0-react";
import dayjs from "dayjs";

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
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [songs, setSongs] = useState<Song[]>([]);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(false);

  const listOptions = [
    { label: "Top 100 Songs", type: "top-100-songs", isSongList: true, isArtistList: false, limit: 100 },
    { label: "Your Top Artists", type: "top-artists", isSongList: false, isArtistList: true, limit: 100 },
    { label: "Top Songs of All Time", type: "top-songs-all-time", isSongList: true, isArtistList: false, limit: 100 },
    { label: "Top 10 Artists", type: "top-10-artists", isSongList: false, isArtistList: true, limit: 10 },
    { label: "Top 10 Songs This Year", type: "top-10-this-year", isSongList: true, isArtistList: false, limit: 10 },
    { label: "Create Custom List", type: "custom", isSongList: false, isArtistList: false, limit: 0 },
  ];

  // Find current option
  const currentOption = listOptions.find(opt => opt.type === listType);

  // Use currentOption for everything
  const isSongList = currentOption?.isSongList ?? false;
  const isArtistList = currentOption?.isArtistList ?? false;
  const limit = currentOption?.limit ?? 100;
  const listLabel = currentOption?.label ?? "List not found";

  // Date filters
  let start: string | undefined;
  let end: string | undefined;

  if (listType === "top-10-this-year") {
    end = dayjs().toISOString();
    start = dayjs().subtract(1, "year").toISOString();
  }

  useEffect(() => {
    const fetchData = async () => {
      if (!isAuthenticated || (!isSongList && !isArtistList)) return;
      setLoading(true);
      try {
        const accessToken = await getAccessTokenSilently();

        const endpoint = isSongList
          ? "/api/lists/songs"
          : "/api/lists/artists";

        const res = await axios.get(endpoint, {
          params: {
            start,
            end,
            limit,
          },
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
          withCredentials: true,
        });

        if (isSongList) {
          setSongs(res.data.songs);
        } else {
          setArtists(res.data.artists);
        }
      } catch (error) {
        setSongs([]);
        setArtists([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [listType, isAuthenticated]);

  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    switch (listType) {
      case "top-100-songs":
      case "top-songs-all-time":
      case "top-10-this-year":
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
        minHeight: "100vh",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background image */}
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

      {/* Main content */}
      <div
        className="card bg-dark text-white shadow rounded-4 p-4"
        style={{ marginTop: "65px", position: "relative", zIndex: 1 }}
      >
        <div className="max-w-4xl mx-auto mt-10 px-4">
          <h1 className="text-2xl font-bold mb-6 text-center capitalize">
            {listLabel}
          </h1>
          <div className="p-4 border rounded-lg shadow">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
