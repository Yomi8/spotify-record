import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import SpotifyUpload from "../components/JSONUpload";
import backgroundImg from "../assets/images/background.jpg";

interface SnapshotJob {
  period: string;
  job_id: string;
}

export default function Settings() {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
  const [snapshotStatus, setSnapshotStatus] = useState<string | null>(null);

  const handleGenerateSnapshots = async () => {
    setSnapshotStatus("Starting snapshot generation...");
    try {
      const token = await getAccessTokenSilently();
      const periodsToGenerate = ["day", "week", "year", "lifetime"];

      const res = await fetch("/api/snapshots/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ periods: periodsToGenerate }),
      });

      if (!res.ok) throw new Error("Failed to start snapshot generation");

      const data = await res.json();

      if (data.jobs && data.jobs.length > 0) {
        const jobsInfo = data.jobs
          .map((job: SnapshotJob) => `Period: ${job.period}, Task ID: ${job.job_id}`)
          .join("\n");
        setSnapshotStatus(`Snapshot generation started for:\n${jobsInfo}`);
      } else {
        setSnapshotStatus("Snapshot generation started.");
      }
    } catch (err) {
      console.error(err);
      setSnapshotStatus("Error starting snapshot generation. Please try again.");
    }
  };

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
                <h1 className="mb-3">Settings</h1>
                <p>You must be logged in to access settings.</p>
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

      {/* Content */}
      <div style={{ position: "relative", zIndex: 2 }}>
        <div className="row justify-content-center">
          <div className="col-md-6">
            {/* Upload Card */}
            <div className="card bg-dark text-white shadow p-4 mb-4">
              <h2 className="mb-3">
                <i className="bi bi-upload me-2"></i> Upload Spotify Data
              </h2>
              <SpotifyUpload />
            </div>

            {/* Snapshots Card */}
            <div className="card bg-dark text-white shadow p-4">
              <h2 className="mb-3">
                <i className="bi bi-bar-chart me-2"></i> Generate Snapshots
              </h2>
              <button
                onClick={handleGenerateSnapshots}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Generate Snapshots Now
              </button>
              {snapshotStatus && (
                <p className="mt-3 text-gray-300 whitespace-pre-line">
                  {snapshotStatus}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}