import { useNavigate } from "react-router-dom";

export default function Lists() {
  const navigate = useNavigate();

  const listOptions = [
    { label: "Top 100 Songs", type: "top-100-songs" },
    { label: "Your Top Artists", type: "top-artists" },
    { label: "Top Songs of All Time", type: "top-songs-all-time" },
    { label: "Top 10 Artists", type: "top-10-artists" },
    { label: "Top 10 Songs This Week", type: "top-10-this-week" },
    { label: "Create Custom List", type: "custom" },
  ];

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
      <div className="max-w-4xl mx-auto mt-10 px-4">
        <h1 className="text-3xl font-bold mb-8 text-center">Lists</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {listOptions.map((list) => (
            <button
              key={list.type}
              onClick={() => navigate(`/lists/${list.type}`)}
              className="bg-blue-600 text-white py-3 px-4 rounded-xl shadow hover:bg-blue-700 transition"
            >
              {list.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
