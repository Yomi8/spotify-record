import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import SpotifyUpload from "../components/JSONUpload";

export default function Settings() {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
  const [snapshotStatus, setSnapshotStatus] = useState<string | null>(null);

  const handleGenerateSnapshots = async () => {
    setSnapshotStatus("Starting snapshot generation...");
    try {
      const token = await getAccessTokenSilently();

      const res = await fetch("/api/snapshots/generate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to start snapshot generation");

      const data = await res.json();
      setSnapshotStatus(`Snapshot generation started (task ID: ${data.task_id})`);
    } catch (err) {
      console.error(err);
      setSnapshotStatus("Error starting snapshot generation. Please try again.");
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="p-4">
        <h1>Settings Page</h1>
        <p>You must be logged in to access settings.</p>
        <button
          onClick={() => loginWithRedirect()}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Log In
        </button>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h1>Settings Page</h1>

      <div className="mt-4">
        <SpotifyUpload />
      </div>

      <div className="mt-6">
        <button
          onClick={handleGenerateSnapshots}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Generate Snapshots Now
        </button>
        {snapshotStatus && <p className="mt-2 text-gray-700">{snapshotStatus}</p>}
      </div>
    </div>
  );
}
