import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import AnalyticsPage from './pages/AnalyticsPage';
import CandidateProfilePage from './pages/CandidateProfilePage';
import DashboardPage from './pages/DashboardPage';
import JobsPage from './pages/JobsPage';
import LandingPage from './pages/LandingPage';
import ReportsPage from './pages/ReportsPage';
import ResultsPage from './pages/ResultsPage';
import ScreeningPage from './pages/ScreeningPage';
import SettingsPage from './pages/SettingsPage';
import UploadPage from './pages/UploadPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/screening" element={<ScreeningPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/candidates/:id" element={<CandidateProfilePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
