import { useNavigate } from "react-router-dom";
import backgroundImg from "../assets/images/background.jpg";

import buttonIMG1 from "../assets/images/buttons/buttonIMG1.jpg";
import buttonIMG2 from "../assets/images/buttons/buttonIMG2.jpg";
import buttonIMG3 from "../assets/images/buttons/buttonIMG3.jpg";
import buttonIMG4 from "../assets/images/buttons/buttonIMG4.jpg";
import buttonIMG5 from "../assets/images/buttons/buttonIMG5.jpg";
import buttonIMG6 from "../assets/images/buttons/buttonIMG6.jpg";

export default function Acknowledgements() {
  const navigate = useNavigate();

  return (
    <div
      className="container-fluid text-white py-4"
      style={{
        minHeight: "100vh",
        position: "relative",
        overflow: "visible",
      }}
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
                maxWidth: "fit-content",
              }}
            >
              <div className="card-body py-3 px-4">
                <h1 className="mb-0">Acknowledgements</h1>
              </div>
            </div>

            {/* Main content card */}
            <div className="card bg-dark text-white shadow p-4">
              {/* Back button inside the card */}
              <button
                className="btn btn-outline-light mb-3"
                style={{
                  width: "85px",
                  textAlign: "left",
                }}
                onClick={() => navigate(-1)}
              >
                <i className="bi bi-arrow-left"></i> Back
              </button>

              {/* Section: Images */}
              <h3 className="mt-3 mb-2">Image Credits</h3>
              <ul className="list-group list-group-flush mb-4">
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG1}
                    alt="Button 1"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 1:</strong> Public Domain - <a href="https://commons.wikimedia.org/wiki/File:1500x1500-abstract-sd2003.jpg" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG2}
                    alt="Button 2"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 2:</strong> Nick Collins - <a href="https://www.pexels.com/photo/blue-painting-1292998/" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG3}
                    alt="Button 3"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 3:</strong> pixel4k - <a href="https://www.pixel4k.com/lines-stripes-shroud-wavy-intermittent-glow-4k-51017.html">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG4}
                    alt="Button 4"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 4:</strong> Public Domain - <a href="https://rare-gallery.com/5323077-line-color-pink-purple-decorative-abstraction-pattern-background-colour-bright-drape-festival-fest-straight-colourful-public-domain-images.html" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG5}
                    alt="Button 5"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 5:</strong> Alen Hunjet - <a href="https://freerangestock.com/photos/143328/abstract-background--spiral-of-blue-lights.html" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={buttonIMG6}
                    alt="Button 6"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Button 6:</strong> FreePik - <a href="https://www.freepik.com/free-photo/blue-color-splash-dark-background-with-copy-space-text_3939420.htm#fromView=keyword&page=1&position=26&uuid=d94107b4-8b7e-4d60-befe-54404980a54b&query=Blue+Abstract+Chaos" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
                <li className="list-group-item bg-dark text-white border-0 d-flex align-items-center">
                  <img
                    src={backgroundImg}
                    alt="Background"
                    style={{
                      width: 40,
                      height: 40,
                      objectFit: "cover",
                      marginRight: 12,
                      borderRadius: 4,
                    }}
                  />
                  <span>
                    <strong>Background:</strong> Public Domain - <a href="https://www.rawpixel.com/image/5923497/photo-image-texture-cloud-aesthetic" target="_blank" rel="noopener noreferrer" className="text-info">Source</a>
                  </span>
                </li>
              </ul>

              {/* Section: APIs */}
              <h3 className="mt-4 mb-2">APIs Used</h3>
              <ul className="list-group list-group-flush mb-4">
                <li className="list-group-item bg-dark text-white border-0">
                  <strong>Spotify Web API:</strong> For fetching track, artist, and
                  album data.
                  <br />
                  <a
                    href="https://developer.spotify.com/documentation/web-api/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-info"
                  >
                    https://developer.spotify.com/documentation/web-api/
                  </a>
                </li>
                {/* Add more APIs here if needed */}
              </ul>

              {/* Section: Other Libraries */}
              <h3 className="mt-4 mb-2">Other Libraries</h3>
              <ul className="list-group list-group-flush">
                <li className="list-group-item bg-dark text-white border-0">
                  <strong>React</strong> &amp; <strong>React Router</strong>
                </li>
                <li className="list-group-item bg-dark text-white border-0">
                  <strong>Bootstrap</strong> for UI styling
                </li>
                {/* Add more libraries if needed */}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
