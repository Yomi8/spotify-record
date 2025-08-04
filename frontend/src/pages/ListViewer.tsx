import { useParams } from "react-router-dom";

import backgroundImg from '../assets/images/background.jpg';

export default function ListViewer() {
  const { listType } = useParams();

  const renderContent = () => {
    switch (listType) {
      case "top-100-songs":
        return <h2>Top 100 Songs Table</h2>;
      case "top-artists":
        return <h2>Your Top Artists Table</h2>;
      case "top-songs-all-time":
        return <h2>Top Songs of All Time Table</h2>;
      case "top-10-artists":
        return <h2>Top 10 Artists Table</h2>;
      case "top-10-this-week":
        return <h2>Top 10 Songs This Week Table</h2>;
      case "custom":
        return <h2>Custom List Builder</h2>;
      default:
        return <h2>List not found</h2>;
    }
  };

  return (
        <div
          className="container-fluid text-white py-4"
          style={{
            minHeight: '100vh',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
            {/* Background image */}
            <img
              src={backgroundImg}
              alt="Abstract Background"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                objectFit: 'cover',
                zIndex: 0,
              }}
            />

            {/* Main content */}
            <div className="card bg-dark text-white shadow rounded-4 p-4" style={{marginTop:'65px', position: 'relative', zIndex: 1 }}>
                <div className="max-w-4xl mx-auto mt-10 px-4">
                  <h1 className="text-2xl font-bold mb-6 text-center capitalize">
                    {listType?.replaceAll("-", " ")}
                  </h1>
                  <div className="p-4 border rounded-lg shadow">{renderContent()}</div>
                </div>
            </div>
        </div>
  );
}
