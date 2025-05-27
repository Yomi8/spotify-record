import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <ul style={styles.ul}>
        <li><Link to="/" style={styles.link}>Home</Link></li>
        <li><Link to="/list" style={styles.link}>List</Link></li>
        <li><Link to="/search" style={styles.link}>Search</Link></li>
        <li><Link to="/settings" style={styles.link}>Settings</Link></li>
      </ul>
    </nav>
  );
}