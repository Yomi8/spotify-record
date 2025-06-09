import { useAuth0 } from "@auth0/auth0-react";
import React, { useState } from "react";

const JSONUpload = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);

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
      if (res.ok) {
        setStatus(`Uploaded: ${json.inserted} new streams`);
      } else {
        setStatus(`Error: ${json.error}`);
      }
    } catch (err) {
      setStatus(`Upload failed: ${err}`);
      console.error(err);
    }
  };

  if (!isAuthenticated) return <p>Please log in to upload your data.</p>;

  return (
    <div className="text-white p-4">
      <h3>Upload your Spotify JSON file</h3>
      <input type="file" accept=".json" onChange={handleChange} className="form-control my-2" />
      <button onClick={handleUpload} className="btn btn-success">Upload</button>
      {status && <p className="mt-2">{status}</p>}
    </div>
  );
};

export default JSONUpload;
