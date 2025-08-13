import { useNavigate } from "react-router-dom";
import backgroundImg from "../assets/images/background.jpg";

import buttonIMG1 from "../assets/images/buttons/buttonIMG1.jpg";
import buttonIMG2 from "../assets/images/buttons/buttonIMG2.png";
import buttonIMG3 from "../assets/images/buttons/buttonIMG3.jpg";
import buttonIMG4 from "../assets/images/buttons/buttonIMG4.jpg";
import buttonIMG5 from "../assets/images/buttons/buttonIMG5.jpg";
import buttonIMG6 from "../assets/images/buttons/buttonIMG6.jpg";

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
      style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}
    >
      {/* Background */}
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

      <div style={{ position: "relative", zIndex: 2, marginTop: "-33px" }}>
        <div className="row justify-content-center">
          <div className="col-md-8">

            {/* Header card */}
            <div
              className="card bg-dark text-white shadow mx-0 mb-4"
              style={{
                borderTopLeftRadius: 0,
                borderTopRightRadius: 0,
                borderBottomLeftRadius: ".5rem",
                borderBottomRightRadius: ".5rem",
              }}
            >
              <div className="card-body py-3 px-4">
                <h1 className="mb-0">Lists</h1>
              </div>
            </div>

            {/* Main content card */}
            <div className="card bg-dark text-white shadow p-4">
              <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-4">
                {listOptions.map((list) => (
                  <div key={list.type} className="d-flex justify-content-center">
                    <button
                      onClick={() => navigate(`/lists/${list.type}`)}
                      className="position-relative d-flex align-items-center justify-content-center rounded-3 shadow-lg overflow-hidden border-0"
                      style={{
                        aspectRatio: "1 / 1",
                        width: "100%",
                        maxWidth: "300px",
                        background: `url(${list.img}) center/cover no-repeat`,
                        color: "white",
                      }}
                    >
                      <div
                        style={{
                          position: "absolute",
                          inset: 0,
                          background: "rgba(0,0,0,0.08)",
                          borderRadius: "inherit",
                          pointerEvents: "none",
                          zIndex: 1,
                        }}
                      />
                      <span
                        className="fw-semibold text-center px-2"
                        style={{
                          position: "relative",
                          zIndex: 2,
                          textShadow: "0 1px 6px rgba(0,0,0,0.35)",
                          fontSize: "1.35rem",
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
      </div>
    </div>
  );
}
