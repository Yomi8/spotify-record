import SpotifyUpload from "../components/JSONUpload";

export default function Settings() {
  return (
    <>
      <h1>Settings Page</h1>
      <div className="mt-4">
        <SpotifyUpload />
      </div>
    </>
  );
}