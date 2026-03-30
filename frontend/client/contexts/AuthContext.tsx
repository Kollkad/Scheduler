// client/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface AuthContextType {
  authChecked: boolean;
  user: { role: string | null } | null;
}

const AuthContext = createContext<AuthContextType>({ authChecked: false, user: null });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<{ role: string | null } | null>(null);

  useEffect(() => {
    fetch('/api/auth/login', { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setUser({ role: data.role });
        }
        setAuthChecked(true);
      })
      .catch(() => setAuthChecked(true));
  }, []);

  return (
    <AuthContext.Provider value={{ authChecked, user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);