import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';

// Mock the components that might cause issues in tests
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock lazy-loaded components
jest.mock('./pages/Dashboard', () => () => <div data-testid="dashboard">Dashboard</div>);
jest.mock('./components/layout/MainLayout', () => ({ children }: { children: React.ReactNode }) => <div>{children}</div>);

test('renders app without crashing', () => {
  render(
    <ThemeProvider theme={theme}>
      <App />
    </ThemeProvider>
  );
  // Just verify it renders without throwing an error
  expect(document.body).toBeTruthy();
});
