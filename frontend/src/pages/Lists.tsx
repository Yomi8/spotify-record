import { useNavigate } from "react-router-dom";
import backgroundImg from '../assets/images/background.jpg';


import buttonIMG1 from '../assets/images/buttons/buttonIMG1.jpg';
import buttonIMG2 from '../assets/images/buttons/buttonIMG2.png';
import buttonIMG3 from '../assets/images/buttons/buttonIMG3.jpg';
import buttonIMG4 from '../assets/images/buttons/buttonIMG4.jpg';
import buttonIMG5 from '../assets/images/buttons/buttonIMG5.jpg';
import buttonIMG6 from '../assets/images/buttons/buttonIMG6.jpg';

export default function Lists() {
  const navigate = useNavigate();

  const listOptions = [
    { label: "Top 100 Songs", type: "top-100-songs", img: buttonIMG1 },
    { label: "Your Top Artists", type: "top-artists", img: buttonIMG2 },
    { label: "Top Songs of All Time", type: "top-songs-all-time", img: buttonIMG3 },
    { label: "Top 10 Artists", type: "top-10-artists", img: buttonIMG4 },
    { label: "Top 10 Songs This Year", type: "top-10-this-year", img: buttonIMG5 },
    { label: "Create Custom List", type: "custom", img: buttonIMG6 },
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
          position: 'fixed',
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
          <div className="row g-4">
            {listOptions.map((list) => (
              <div
                key={list.type}
                className="col-12 col-sm-6 col-md-4 col-lg-3 d-flex justify-content-center mb-4"
              >
                <button
                  onClick={() => navigate(`/lists/${list.type}`)}
                  className="position-relative d-flex align-items-center justify-content-center rounded-3 shadow-lg overflow-hidden border-0"
                  style={{
                    aspectRatio: '1 / 1',
                    maxWidth: '300px',
                    height: '300px',
                    minHeight: '0',
                    background: `url(${list.img}) center/cover no-repeat`,
                    color: 'white',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'rgba(0,0,0,0.08)',
                      borderRadius: 'inherit',
                      pointerEvents: 'none',
                      zIndex: 1,
                    }}
                  />
                  <span
                    className="fw-semibold text-center px-2"
                    style={{
                      position: 'relative',
                      zIndex: 2,
                      textShadow: '0 1px 6px rgba(0,0,0,0.35)',
                      fontSize: '1.35rem',
                    }}
                  >
                    {list.label}
                  </span>
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}