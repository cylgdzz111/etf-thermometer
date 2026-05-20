import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Market } from '../types';

interface MarketContextValue {
  market: Market;
  setMarket: (m: Market) => void;
}

const MarketContext = createContext<MarketContextValue | null>(null);

export function MarketProvider({ children }: { children: ReactNode }) {
  const [market, setMarketState] = useState<Market>(() => {
    const saved = localStorage.getItem('etf-market');
    return (saved as Market) ?? 'cn';
  });

  useEffect(() => {
    localStorage.setItem('etf-market', market);
  }, [market]);

  function setMarket(m: Market) {
    setMarketState(m);
  }

  return (
    <MarketContext.Provider value={{ market, setMarket }}>
      {children}
    </MarketContext.Provider>
  );
}

export function useMarket() {
  const ctx = useContext(MarketContext);
  if (!ctx) throw new Error('useMarket must be used within MarketProvider');
  return ctx;
}
