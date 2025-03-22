import { createTheme, ThemeOptions } from '@mui/material/styles';
import { palette } from './palette';
import { components } from './components';
import { typography } from './typography';

const themeOptions: ThemeOptions = {
  palette,
  typography,
  components,
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
};

const theme = createTheme(themeOptions);

export default theme;

