import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MarketProvider } from './store/MarketContext';
import Nav from './components/ui/Nav';
import Dashboard from './pages/Dashboard';
import IndexList from './pages/IndexList';
import Detail from './pages/Detail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MarketProvider>
        <BrowserRouter>
          <div className="app">
            <Nav />
            <main className="page">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/list" element={<IndexList />} />
                <Route path="/detail/:code" element={<Detail />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </MarketProvider>
    </QueryClientProvider>
  );
}
