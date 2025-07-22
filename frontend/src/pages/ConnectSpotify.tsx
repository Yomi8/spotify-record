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
          redirect: "manual",
        });

        if (res.status === 302 || res.status === 301) {
          const redirectUrl = res.headers.get("Location");
          if (redirectUrl) {
            window.location.href = redirectUrl;
            return;
          } else {
            console.error("Redirect location header missing");
            return;
          }
        }

        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          const json = await res.json();
          console.error("Unexpected JSON response:", json);
        } else if (contentType.includes("text/html")) {
          // Try to extract the redirect URL from the HTML
          const text = await res.text();
          const match = text.match(/<a href="([^"]+)"/);
          if (match && match[1]) {
            window.location.href = match[1];
            return;
          }
          console.error("Unexpected HTML response, could not find redirect URL:", text);
        } else {
          const text = await res.text();
          if (!text) {
            console.error(
              `Unexpected empty response. Status: ${res.status}, Headers:`,
              Object.fromEntries(res.headers.entries())
            );
          } else {
            console.error("Unexpected response:", text);
          }
        }

      } catch (err) {
        console.error("Error connecting to Spotify:", err);
      }
    }

    connectSpotify();
  }, [getAccessTokenSilently]);

  return <p>Redirecting to Spotify...</p>;
}
