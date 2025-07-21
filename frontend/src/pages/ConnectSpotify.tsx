import { useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";

export default function ConnectSpotify() {
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    async function connectSpotify() {
      try {
        const token = await getAccessTokenSilently();

        // Call backend login route with Authorization header
        const res = await fetch("https://yomi16.nz/api/spotify/login", {
          headers: { Authorization: `Bearer ${token}` },
          redirect: "manual",  // do not auto-follow redirects in fetch
        });

        if (res.status === 302 || res.status === 301) {
          const redirectUrl = res.headers.get("Location");
          if (redirectUrl) {
            // Redirect the browser to Spotify login page
            window.location.href = redirectUrl;
          } else {
            console.error("Redirect location header missing");
          }
        } else {
          const json = await res.json();
          console.error("Unexpected response:", json);
        }
      } catch (err) {
        console.error("Error connecting to Spotify:", err);
      }
    }

    connectSpotify();
  }, [getAccessTokenSilently]);

  return <p>Redirecting to Spotify...</p>;
}
