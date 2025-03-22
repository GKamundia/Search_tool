import { PaletteOptions } from '@mui/material/styles';

// Research frontend color palette based on CEMA Style Guide
export const palette: PaletteOptions = {
  primary: {
    main: '#003366',      // Deep blue as primary color
    light: '#335C85',
    dark: '#00264D',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#FF9E1B',      // Orange accent
    light: '#FFBE5C',
    dark: '#CC7E16',
    contrastText: '#000000',
  },
  success: {
    main: '#4CAF50',
    light: '#81C784',
    dark: '#388E3C',
  },
  warning: {
    main: '#FF9800',
    light: '#FFB74D',
    dark: '#F57C00',
  },
  error: {
    main: '#F44336',
    light: '#E57373',
    dark: '#D32F2F',
  },
  info: {
    main: '#2196F3',
    light: '#64B5F6',
    dark: '#1976D2',
  },
  grey: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
  background: {
    default: '#F8F9FA',
    paper: '#FFFFFF',
  },
  text: {
    primary: '#212121',
    secondary: '#757575',
    disabled: '#9E9E9E',
  },
};

