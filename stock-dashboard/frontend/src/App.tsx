import React from 'react';
import Dashboard from './pages/Dashboard';
import { StockProvider } from './store/stock_store';
import './styles/App.css';

function App() {
  return (
    <StockProvider>
      <Dashboard />
    </StockProvider>
  );
}

export default App;
