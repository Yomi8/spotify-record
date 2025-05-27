import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <ul style={styles.ul}>
        <li><Link to="/" >Home</Link></li>
        <li><Link to="/list" >List</Link></li>
        <li><Link to="/search" >Search</Link></li>
        <li><Link to="/settings" >Settings</Link></li>
      </ul>
    </nav>
  );
}