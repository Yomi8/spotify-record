import { useParams } from "react-router-dom";

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
    <div className="max-w-4xl mx-auto mt-10 px-4">
      <h1 className="text-2xl font-bold mb-6 text-center capitalize">
        {listType?.replaceAll("-", " ")}
      </h1>
      <div className="p-4 border rounded-lg shadow">{renderContent()}</div>
    </div>
  );
}
