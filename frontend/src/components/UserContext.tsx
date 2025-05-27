import { createContext, PropsWithChildren, useState, useContext, useEffect } from 'react';

interface UserContextType {
  token: string | null;
  isLoggedIn: boolean;
  login: (jwt: string) => void;
  logout: () => void;
}

const UserContext = createContext<UserContextType>({
  token: null,
  isLoggedIn: false,
  login: () => {},
  logout: () => {},
});

export function UserProvider({ children }: PropsWithChildren<{}>) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const isLoggedIn = !!token;

  const login = (jwt: string) => {
    localStorage.setItem('token', jwt);
    setToken(jwt);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) setToken(storedToken);
  }, []);

  return (
    <UserContext.Provider value={{ token, isLoggedIn, login, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}