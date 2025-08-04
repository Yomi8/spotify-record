import { useNavigate } from "react-router-dom";
import backgroundImg from '../assets/images/background.jpg';

// Example images, replace with your own
// import top100Img from '../assets/images/top100.jpg';
// import artistsImg from '../assets/images/artists.jpg';
// import allTimeImg from '../assets/images/alltime.jpg';
// import top10Img from '../assets/images/top10.jpg';
// import weekImg from '../assets/images/week.jpg';
// import customImg from '../assets/images/custom.jpg';

export default function Lists() {
  const navigate = useNavigate();

  const listOptions = [
    { label: "Top 100 Songs", type: "top-100-songs", img: top100Img },
    { label: "Your Top Artists", type: "top-artists", img: artistsImg },
    { label: "Top Songs of All Time", type: "top-songs-all-time", img: allTimeImg },
    { label: "Top 10 Artists", type: "top-10-artists", img: top10Img },
    { label: "Top 10 Songs This Week", type: "top-10-this-week", img: weekImg },
    { label: "Create Custom List", type: "custom", img: customImg },
  ];

  return (
    <div
      className="container-fluid text-white py-4"
      style={{
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
      }}>
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
          <h1 className="text-3xl font-bold mb-8 text-center">Lists</h1>
          <div
            className="
              grid
              grid-cols-1
              sm:grid-cols-2
              md:grid-cols-3
              lg:grid-cols-4
              gap-6
            "
          >
            {listOptions.map((list) => (
              <button
                key={list.type}
                onClick={() => navigate(`/lists/${list.type}`)}
                className="relative flex items-center justify-center rounded-2xl shadow-lg overflow-hidden transition hover:scale-105"
                style={{
                  aspectRatio: '1 / 1',
                  width: '100%',
                  minHeight: '0',
                  background: `url(${list.img}) center/cover no-repeat`,
                  color: 'white',
                  border: 'none',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(0,0,0,0.45)',
                    borderRadius: 'inherit',
                  }}
                />
                <span className="relative z-10 text-lg font-semibold text-center px-2">
                  {list.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}