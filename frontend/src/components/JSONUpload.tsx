import { useAuth0 } from "@auth0/auth0-react";
import React, { useEffect, useState } from "react";

const JSONUpload = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setStatus("Uploading...");
    setResult(null);

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

      if (res.status === 202 && json.job_id) {
        setJobId(json.job_id);
        setStatus("Processing...");
      } else {
        setStatus(`Error: ${json.error || "Unknown error"}`);
        setIsUploading(false);
      }
    } catch (err) {
      setStatus(`Upload failed: ${(err as Error).message}`);
      console.error(err);
      setIsUploading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`https://yomi16.nz/api/job-status/${jobId}`);
        const data = await res.json();

        const jobStatus = data.status;
        setStatus(jobStatus);

        if (jobStatus === "finished") {
          clearInterval(interval);
          setResult(data.result);
          setIsUploading(false);
        } else if (jobStatus === "failed") {
          clearInterval(interval);
          setResult({ error: data.error || "Job failed" });
          setIsUploading(false);
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(interval);
        setStatus("Polling error");
        setResult({ error: (err as Error).message });
        setIsUploading(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!isAuthenticated) {
    return <p className="text-danger">Please log in to upload your data.</p>;
  }

  const renderResult = () => {
    if (!result) return null;

    if (result.error) {
      return (
        <div className="alert alert-danger mt-3">
          <strong>Error:</strong> {result.error}
        </div>
      );
    }

    return (
      <div className="card bg-dark text-white mt-3">
        <div className="card-body">
          <h5 className="card-title">Upload Complete</h5>
          <table className="table table-sm table-dark table-bordered mb-0">
            <tbody>
              <tr>
                <th scope="row">Status</th>
                <td
                  className={
                    result.status === "COMPLETE" ? "text-success" : "text-warning"
                  }
                >
                  {result.status}
                </td>
              </tr>
              <tr>
                <th scope="row">Inserted</th>
                <td>{result.inserted}</td>
              </tr>
              <tr>
                <th scope="row">Total</th>
                <td>{result.total}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="text-white">
      <h4 className="mb-3">
        Upload Spotify JSON Data from Your Extended Listening History
      </h4>

      <input
        type="file"
        accept=".json"
        onChange={handleChange}
        className="form-control mb-3"
        disabled={isUploading}
      />

      <button
        onClick={handleUpload}
        className="btn btn-success d-flex align-items-center"
        disabled={!file || isUploading}
      >
        {isUploading && (
          <span
            className="spinner-border spinner-border-sm me-2"
            role="status"
            aria-hidden="true"
          ></span>
        )}
        {isUploading ? "Processing..." : "Upload"}
      </button>

      {status && (
        <div className="mt-3">
          <span className="fw-bold">Status: </span>
          <span
            className={
              status === "finished"
                ? "text-success"
                : status === "failed"
                ? "text-danger"
                : status === "Processing..." || status === "Uploading..."
                ? "text-warning"
                : "text-info"
            }
          >
            {status}
          </span>
        </div>
      )}

      {renderResult()}
    </div>
  );
};

export default JSONUpload;