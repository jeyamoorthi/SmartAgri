import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import SignUp from './pages/SignUp';
import Login from './pages/Login';
import Home from './pages/Home';
import VoiceConsultant from './pages/VoiceConsultant';
import DashboardLayout from './components/DashboardLayout';
import MarketPage from './pages/MarketPage';
import PestPage from './pages/PestPage';
import RecommendationsPage from './pages/RecommendationsPage';
import DiseasePage from './pages/DiseasePage';

// Protected Route Guard
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('smartagri_token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

// Auto-Redirect if logged in
const AuthRoute = ({ children }) => {
  const token = localStorage.getItem('smartagri_token');
  if (token) return <Navigate to="/voice-consultant" replace />;
  return children;
};

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <div className="bg-gray-100 min-h-screen text-[var(--text-900)]">
          <Routes>
            <Route path="/" element={<Navigate to="/signup" replace />} />
            
            <Route 
              path="/signup" 
              element={
                <AuthRoute>
                  <SignUp />
                </AuthRoute>
              } 
            />
            
            <Route 
              path="/login" 
              element={
                <AuthRoute>
                  <Login />
                </AuthRoute>
              } 
            />
            
            {/* Main navigable app layout with persistent voice FAB */}
            <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
              <Route path="/home" element={<Home />} />
              <Route path="/market" element={<MarketPage />} />
              <Route path="/pest" element={<PestPage />} />
              <Route path="/disease" element={<DiseasePage />} />
              <Route path="/recommendations" element={<RecommendationsPage />} />
              <Route path="/voice-consultant" element={<VoiceConsultant />} />
            </Route>

            <Route path="*" element={<Navigate to="/voice-consultant" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </LanguageProvider>
  );
}

export default App;
