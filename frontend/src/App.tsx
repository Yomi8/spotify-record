import 'bootstrap/dist/css/bootstrap.css'

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import UserSync from './components/UserSync';

import Home from './pages/Home';
import List from './pages/Lists';
import Search from './pages/Search';
import Settings from './pages/Settings';
import Profile from './pages/Profile';

import ConnectSpotify from './pages/ConnectSpotify';

function App() {
  return (
    <Router>
      <Navbar />
      <UserSync />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/list" element={<List />} />
        <Route path="/search" element={<Search />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/connect-spotify" element={<ConnectSpotify />} /> 
      </Routes>
    </Router>
  );
}

export default App;