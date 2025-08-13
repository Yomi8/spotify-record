import { useState } from "react";
import type { ReactNode } from "react";
import backgroundImg from "../assets/images/background.jpg";

import step1Img from "../assets/images/help/step1.png";
import step2Img from "../assets/images/help/step2.png";
import step3Img from "../assets/images/help/step3.png";
import step4Img from "../assets/images/help/step4.png";
import step5Img from "../assets/images/help/step5.png";
import step6Img from "../assets/images/help/step6.png";

type Step = {
  title: string;
  text?: ReactNode;
  bullets?: string[];
  img?: string;
};

export default function Help() {
  const [openGuide, setOpenGuide] = useState(false); // guide card collapsed/expanded
  const [openTemplate, setOpenTemplate] = useState(false);

  const steps: Step[] = [
    {
      title: "Step 1 — Go to Spotify's Privacy Settings",
      text: (
        <>
          Open Spotify’s Privacy Settings page:{" "}
          <a
            href="https://www.spotify.com/account/privacy/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-decoration-underline"
          >
            https://www.spotify.com/account/privacy/
          </a>
          . Scroll down until you see the “Download your data” section.
        </>
      ),
      img: step1Img,
    },
    {
      title: "Step 2 — Request Extended Streaming History",
      text:
        "Under “Extended streaming history”, click “Request data” and confirm in the email Spotify sends you. This ensures you get your full listening history, not just the last few months. Spotify will email you again when your file is ready (this can take a few days).",
      img: step2Img,
    },
    {
      title: "Step 3 — Download Your Data",
      text:
        "When you get Spotify’s ready email, click the download link, log in if asked, and download the .zip file. Save it somewhere easy to find.",
      img: step3Img,
    },
    {
      title: "Step 4 — Getting the Right Files",
      text:
        "Open the .zip file. Look for one or more JSON files named “StreamingHistory.json” or “StreamingHistory0.json”, “StreamingHistory1.json”, etc. These contain your listening history.",
      img: step4Img,
    },
    {
      title: "Step 5 — Log In and Open Settings",
      text:
        "Log in to your account here, and choose “Settings” from your profile menu (top-right).",
      img: step5Img,
    },
    {
      title: "Step 6 — Upload Your Data",
      text:
        "In Settings, use “Upload Spotify Data”. Click “Choose File”, select one of the JSON files from Step 4, then click “Upload”. Processing may take a few minutes depending on file size. Note: only one file can be uploaded at a time.",
      img: step6Img,
    },
  ];

  return (
    <div
      className="container-fluid text-white py-4"
      style={{ minHeight: "100vh", position: "relative", overflow: "visible" }}
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

      {/* Content */}
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
                <h1 className="mb-0">Help</h1>
              </div>
            </div>

            {/* Collapsible card: All steps in ONE card */}
            <div className="card bg-dark text-white shadow mt-0 mb-2 rounded-4">
              <button
                className="w-100 text-start p-4 d-flex justify-content-between align-items-center bg-dark border-0"
                onClick={() => setOpenGuide((v) => !v)}
                aria-expanded={openGuide}
                aria-controls="guide-body"
                style={{ cursor: "pointer" }}
              >
                <span className="h4 text-white m-0">
                  <i className="bi bi-cloud-arrow-up me-2" /> How do I download and upload my Spotify data?
                </span>
                <i className={`bi ms-3 text-white ${openGuide ? "bi-chevron-up" : "bi-chevron-down"}`} />
              </button>

              {openGuide && (
                <div id="guide-body" className="px-4 pb-4">
                  {steps.map((step, index) => (
                    <div key={index} className="card bg-secondary text-white shadow-sm p-3 mb-3">
                      <h5 className="mb-3">{step.title}</h5>
                      <div className="row align-items-center g-3">
                        <div className="col-md-6">
                          {step.bullets ? (
                            <ul className="mb-0">
                              {step.bullets.map((b, i) => (
                                <li key={i}>{b}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="mb-0">{step.text}</p>
                          )}
                        </div>
                        {step.img && (
                          <div className="col-md-6">
                            <img
                              src={step.img}
                              alt={step.title}
                              className="img-fluid rounded shadow"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Example of another collapsible FAQ card (placeholder) */}
            <div className="card bg-dark text-white shadow mb-2 rounded-4">
              <button
                className="w-100 text-start p-4 d-flex justify-content-between align-items-center bg-dark border-0"
                onClick={() => setOpenTemplate(v => !v)}
                aria-expanded={openTemplate}
                aria-controls="files-faq-body"
                style={{ cursor: "pointer" }}
              >
                <span className="h4 text-white m-0">
                  <i className="bi bi-gear-wide-connected me-2" /> Template for another FAQ
                </span>
                <i className={`bi ms-3 text-white ${openTemplate ? "bi-chevron-up" : "bi-chevron-down"}`} />
              </button>

              {openTemplate && (
                <div id="files-faq-body" className="px-4 pb-4">
                  <p className="mt-3 mb-0 text-gray-300">
                    Example of some text
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
