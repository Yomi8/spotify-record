import 'bootstrap/dist/css/bootstrap.css'

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import UserSync from './components/UserSync';
import Footer from './components/Footer';

import Home from './pages/Home';
import Lists from "./pages/Lists";
import ListViewer from "./pages/ListViewer";
import Search from './pages/Search';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import SongDetails from './pages/SongDetails';
import ArtistDetails from './pages/ArtistDetails';

function App() {
  return (
    <Router>
      <Navbar />
      <UserSync />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/lists" element={<Lists />} />
        <Route path="/lists/:listType" element={<ListViewer />} />
        <Route path="/search" element={<Search />} />
        <Route path="/song/:songId" element={<SongDetails />} />
        <Route path="/artist/:artistId" element={<ArtistDetails />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
      <Footer />
    </Router>
  );
}

export default App;