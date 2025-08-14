import { useAuth0 } from "@auth0/auth0-react";
import backgroundImg from "../assets/images/background.jpg";

import step1Img from "../assets/images/help/step1.png";
import step2Img from "../assets/images/help/step2.png";
import step3Img from "../assets/images/help/step3.png";
import step4Img from "../assets/images/help/step4.png";
import step5Img from "../assets/images/help/step5.png";
import step6Img from "../assets/images/help/step6.png";


export default function Help() {
  const { isAuthenticated, loginWithRedirect } = useAuth0();

  const steps = [
    {
      title: "Step 1 — Go to Spotify's Privacy Settings",
      text: `Open Spotify’s Privacy Settings page: https://www.spotify.com/account/privacy/ Scroll down until you see the "Download your data" section.`,
      img: step1Img,
    },
    {
      title: "Step 2 — Request Extended Streaming History",
      text: `Under "Extended streaming history", click "Request data" and confirm from you email. This ensures you get your full listening history, not just the last few months. Spotify will email you when your file is ready (this can take a few days).`,
      img: step2Img,
    },
    {
      title: "Step 3 — Download Your Data File",
      text: `When you get Spotify’s email, click the download link, log in if asked, and download the .zip file. 
Save it somewhere easy to find.`,
      img: step3Img,
    },
    {
      title: "Step 4 — Find the Right File Inside",
      text: `Open the .zip file. Look for one or more JSON files named "StreamingHistory.json" or "StreamingHistory0.json", "StreamingHistory1.json", etc. These contain your listening history. For a detailed look at what these files contain, Spotify provide a PDF with information about each field.`,
      img: step4Img,
    },
    {
      title: "Step 5 — Log In and View Settings",
      text: `Log in to your account, and select 'Settings' from the profile dropdown in the top right of the site.`,
      img: step5Img,
    },
    {
      title: "Step 6 — Upload Your Data",
      text: "In the settings page, use the 'Upload Spotify Data' section and click browse to select one of the JSON files from Step 4. Once the file has been selected you can click the upload button to start the upload process. The upload may take a few minutes depending on the size of the file. Note: only one file can be uploaded at a time.",
      img: step6Img,
    },
    {
      title: "Troubleshooting",
      text: `• Can't find the file? Make sure you extracted the .zip.\n
• Upload error? Ensure you’re uploading a JSON file, not the zip.\n
• Data looks short? Spotify may have only included recent months unless you requested extended history.`,
      img: "",
    },
  ];

  if (!isAuthenticated) {
    return (
      <div
        className="container-fluid text-white py-4"
        style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}
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
        {/* Overlay */}
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "rgba(0,0,0,0.5)",
            zIndex: 1,
          }}
        />
        {/* Content */}
        <div style={{ position: "relative", zIndex: 2 }}>
          <div className="row justify-content-center">
            <div className="col-md-6">
              <div className="card bg-dark text-white shadow p-4">
                <h1 className="mb-3">Help</h1>
                <p>You must be logged in to view the help guide.</p>
                <button
                  onClick={() => loginWithRedirect()}
                  className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Log In
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
      {/* Overlay */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background: "rgba(0,0,0,0.5)",
          zIndex: 1,
        }}
      />
      {/* Content */}
      <div style={{ position: "relative", zIndex: 2 }}>
        <div className="row justify-content-center">
          <div className="col-md-8">
            {steps.map((step, index) => (
              <div key={index} className="card bg-dark text-white shadow p-4 mb-4">
                <h2 className="mb-3">{step.title}</h2>
                <div className="row align-items-center">
                  <div className="col-md-6">
                    <p>{step.text}</p>
                  </div>
                  <div className="col-md-6">
                    <img
                      src={step.img}
                      alt={step.title}
                      className="img-fluid rounded shadow"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
