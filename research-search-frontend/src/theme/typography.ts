import { TypographyOptions } from '@mui/material/styles/createTypography';

// Typography settings based on CEMA Style Guide
export const typography: TypographyOptions = {
  fontFamily: [
    'Roboto',
    '"Segoe UI"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: {
    fontWeight: 700,
    fontSize: '2.5rem',
    lineHeight: 1.2,
    letterSpacing: '-0.01562em',
  },
  h2: {
    fontWeight: 700,
    fontSize: '2rem',
    lineHeight: 1.3,
    letterSpacing: '-0.00833em',
  },
  h3: {
    fontWeight: 600,
    fontSize: '1.75rem',
    lineHeight: 1.3,
    letterSpacing: '0em',
  },
  h4: {
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.35,
    letterSpacing: '0.00735em',
  },
  h5: {
    fontWeight: 500,
    fontSize: '1.25rem',
    lineHeight: 1.4,
    letterSpacing: '0em',
  },
  h6: {
    fontWeight: 500,
    fontSize: '1.125rem',
    lineHeight: 1.4,
    letterSpacing: '0.0075em',
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
    letterSpacing: '0.00938em',
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.55,
    letterSpacing: '0.01071em',
  },
  button: {
    fontWeight: 500,
    fontSize: '0.875rem',
    lineHeight: 1.75,
    letterSpacing: '0.02857em',
    textTransform: 'uppercase',
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.66,
    letterSpacing: '0.03333em',
  },
};

