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
            window.location.href = redirectUrl;
          } else {
            console.error("Redirect location header missing");
          }
        } else if (res.headers.get("content-type")?.includes("application/json")) {
          const json = await res.json();
          console.error("Unexpected JSON response:", json);
        } else {
          // Maybe HTML or empty response - just log text instead
          const text = await res.text();
          console.error("Unexpected response:", text);
        }

      } catch (err) {
        console.error("Error connecting to Spotify:", err);
      }
    }

    connectSpotify();
  }, [getAccessTokenSilently]);

  return <p>Redirecting to Spotify...</p>;
}
