import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import App from './App.tsx'
import { Auth0Provider } from '@auth0/auth0-react';

const domain = 'dev-id5fm2bqd16i1nrv.au.auth0.com';
const clientId = '6K1X0Vpq494HT8sX63LtewqCCEYL5kFM';
const serverIp = '109.123.227.242';


createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: `http://${serverIp}:3000/callback`,
      }}
    >
      <App />
    </Auth0Provider>
  </React.StrictMode>
)
