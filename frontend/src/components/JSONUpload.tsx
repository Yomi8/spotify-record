import { useAuth0 } from "@auth0/auth0-react";
import React, { useEffect, useState } from "react";

const JSONUpload = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [file, setFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      const token = await getAccessTokenSilently();

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("https://yomi16.nz/api/upload-spotify-json", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const json = await res.json();

      if (res.status === 202 && json.task_id) {
        setTaskId(json.task_id);
        setStatus("Processing...");
        setProgress(null);
        setResult(null);
      } else {
        setStatus(`Error: ${json.error || "Unknown error"}`);
      }
    } catch (err) {
      setStatus(`Upload failed: ${err}`);
      console.error(err);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`https://yomi16.nz/api/task-status/${taskId}`);
        const data = await res.json();

        setStatus(data.status);
        if (data.progress?.progress_pct != null) {
          setProgress(data.progress.progress_pct);
        }

        if (data.status === "SUCCESS" || data.status === "FAILURE") {
          clearInterval(interval);
          setResult(data.result || data.progress || {});
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(interval);
        setStatus("Error polling status.");
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId]);

  if (!isAuthenticated) return <p>Please log in to upload your data.</p>;

  return (
    <div className="text-white p-4">
      <h3 className="text-xl mb-2">Upload your Spotify JSON file</h3>
      <input
        type="file"
        accept=".json"
        onChange={handleChange}
        className="form-control my-2"
      />
      <button onClick={handleUpload} className="btn btn-success">
        Upload
      </button>

      {status && <p className="mt-4 text-info">Status: {status}</p>}
      {progress !== null && <p className="mt-2">Progress: {progress}%</p>}
      {result && (
        <div className="mt-3">
          <h4>Result</h4>
          <pre className="bg-dark p-2 rounded text-white">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default JSONUpload;
