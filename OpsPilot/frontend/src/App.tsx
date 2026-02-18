import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Tasks } from './pages/Tasks';
import { Tools } from './pages/Tools';
import { SOP } from './pages/SOP';
import { Agents } from './pages/Agents';
import { Tracing } from './pages/Tracing';
import { Settings } from './pages/Settings';
import { Scheduler } from './pages/Scheduler';
import { Analytics } from './pages/Analytics';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/sop" element={<SOP />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/tracing" element={<Tracing />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/scheduler" element={<Scheduler />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
