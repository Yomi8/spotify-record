import { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

export default function ConnectSpotify() {
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    const connect = async () => {
      const token = await getAccessTokenSilently();
      const res = await fetch('https://yomi16.nz/api/spotify/login', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.redirected) {
        // Redirect user to Spotify auth
        window.location.href = res.url;
      } else {
        const json = await res.json();
        console.error('Unexpected response:', json);
      }
    };

    connect();
  }, [getAccessTokenSilently]);

  return <p>Redirecting to Spotify...</p>;
}
