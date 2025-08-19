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
import SongDetails from './pages/SongDetails';
import ArtistDetails from './pages/ArtistDetails';
import Help from './pages/Help';
import Acknowledgements from './pages/Acknowledgements';

function App() {
  return (
    <Router>
      <Navbar />
      <UserSync />
      <div style={{ paddingTop: '65px', paddingBottom: '50px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lists" element={<Lists />} />
          <Route path="/lists/:listType" element={<ListViewer />} />
          <Route path="/search" element={<Search />} />
          <Route path="/song/:songId" element={<SongDetails />} />
          <Route path="/artist/:artistId" element={<ArtistDetails />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="/acknowledgements" element={<Acknowledgements />} />
        </Routes>
      </div>
      <Footer />
    </Router>
  );
}

export default App;