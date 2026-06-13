import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Chat } from '@/pages/chat';
import { Status } from '@/pages/status';
import { Apps } from '@/pages/apps';
import { Help } from '@/pages/help';
import { About } from '@/pages/about';
import { Settings } from '@/pages/settings';
import { Control } from '@/pages/control';
import Logging from '@/pages/Logging';

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/control" element={<Control />} />
          <Route path="/about" element={<About />} />
          <Route path="/logs" element={<Logging />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
