import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="p-8 text-center text-slate-400">API Sentinel Dashboard Initializing...</div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
