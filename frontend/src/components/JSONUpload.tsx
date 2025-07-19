import { useAuth0 } from "@auth0/auth0-react";
import React, { useEffect, useState } from "react";

const JSONUpload = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [file, setFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
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
        setResult(null);
      } else {
        setStatus(`Error: ${json.error || "Unknown error"}`);
      }
    } catch (err) {
      setStatus(`Upload failed: ${(err as Error).message}`);
      console.error(err);
    }
  };

  useEffect(() => {
    if (!taskId) return;
  
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`https://yomi16.nz/api/job-status/${taskId}`);
        const data = await res.json();
      
        const jobStatus = data.status;
        setStatus(jobStatus);
      
        if (jobStatus === "finished") {
          clearInterval(interval);
          setResult(data.result);
        } else if (jobStatus === "failed") {
          clearInterval(interval);
          setResult({ error: data.error || "Job failed" });
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(interval);
        setStatus("Polling error");
        setResult({ error: (err as Error).message });
      }
    }, 3000);
  
    return () => clearInterval(interval);
  }, [taskId]);

  if (!isAuthenticated) {
    return <p className="text-danger">Please log in to upload your data.</p>;
  }

  return (
    <div className="text-white p-4">
      <h3 className="text-xl mb-2">Upload your Spotify JSON file</h3>

      <input
        type="file"
        accept=".json"
        onChange={handleChange}
        className="form-control my-2"
      />

      <button
        onClick={handleUpload}
        className="btn btn-success"
        disabled={!file}
      >
        Upload
      </button>

      {status && <p className="mt-4 text-info">Status: {status}</p>}

      {result && (
        <div className="mt-3">
          <h4 className="text-lg">{result.error ? "Error" : "Result"}</h4>
          <pre className="bg-dark p-2 rounded text-white overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default JSONUpload;
