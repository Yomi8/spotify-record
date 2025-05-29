import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

export default function Home() {
  const { user, isAuthenticated } = useAuth0();

  return (
    <div
      className="container-fluid text-white py-4"
      style={{ minHeight: '100vh', background: 'linear-gradient(to right, #000, #333)' }}
    >
      <h1>
        Welcome{' '}
        <span className="text-muted">
          {isAuthenticated
            ? user.nickname || user.name || user.email
            : 'Guest'}
        </span>
        !
      </h1>

      <div className="row mt-4">
        {/* Left card */}
        <div className="col-md-6">
          <div className="card bg-dark text-white shadow">
            <div className="card-header">
              <i className="bi bi-star me-2"></i> Quick Bits
            </div>
            <div className="card-body">
              <p>Info</p>
            </div>
          </div>
        </div>

        {/* Right background image placeholder */}
        <div className="col-md-6 d-flex align-items-center justify-content-center">
          <div className="text-center text-secondary">
            <i className="bi bi-image" style={{ fontSize: '4rem' }}></i>
            <p>{'{Abstract Background}'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}