import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  useTheme,
  Collapse
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import BookmarksIcon from '@mui/icons-material/Bookmarks';
import NewReleasesIcon from '@mui/icons-material/NewReleases';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpIcon from '@mui/icons-material/Help';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import ScienceIcon from '@mui/icons-material/Science';
import LocalLibraryIcon from '@mui/icons-material/LocalLibrary';
import ArticleIcon from '@mui/icons-material/Article';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: "permanent" | "persistent" | "temporary";
}

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant }) => {
  const theme = useTheme();
  const location = useLocation();
  const [databasesOpen, setDatabasesOpen] = React.useState(false);

  const handleDatabasesClick = () => {
    setDatabasesOpen(!databasesOpen);
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const sidebarContent = (
    <Box
      sx={{
        width: 250,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box
          component="img"
          sx={{
            height: 40,
            width: 'auto',
          }}
          alt="Academic Search Portal Logo"
          src="/logo.png"
          // Fallback to text if logo not available
          onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
            e.currentTarget.style.display = 'none';
          }}
        />
      </Box>
      
      <List sx={{ width: '100%', flexGrow: 1 }} component="nav">
        <ListItemButton
          component={Link} 
          to="/"
          selected={isActive('/')}
        >
          <ListItemIcon>
            <DashboardIcon color={isActive('/') ? 'primary' : 'inherit'} />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItemButton>
        
        <ListItemButton
          component={Link} 
          to="/search"
          selected={isActive('/search')}
        >
          <ListItemIcon>
            <SearchIcon color={isActive('/search') ? 'primary' : 'inherit'} />
          </ListItemIcon>
          <ListItemText primary="Search" />
        </ListItemButton>
        
        <ListItemButton
          component={Link} 
          to="/saved-searches"
          selected={isActive('/saved-searches')}
        >
          <ListItemIcon>
            <BookmarksIcon color={isActive('/saved-searches') ? 'primary' : 'inherit'} />
          </ListItemIcon>
          <ListItemText primary="Saved Searches" />
        </ListItemButton>
        
        <ListItemButton
          component={Link} 
          to="/new-papers"
          selected={isActive('/new-papers')}
        >
          <ListItemIcon>
            <NewReleasesIcon color={isActive('/new-papers') ? 'primary' : 'inherit'} />
          </ListItemIcon>
          <ListItemText primary="New Papers" />
        </ListItemButton>
        
        <ListItemButton onClick={handleDatabasesClick}>
          <ListItemIcon>
            <LocalLibraryIcon />
          </ListItemIcon>
          <ListItemText primary="Databases" />
          {databasesOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        
        <Collapse in={databasesOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItemButton sx={{ pl: 4 }}>
              <ListItemIcon>
                <ScienceIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="PubMed" />
            </ListItemButton>
            
            <ListItemButton sx={{ pl: 4 }}>
              <ListItemIcon>
                <ArticleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="arXiv" />
            </ListItemButton>
            
            <ListItemButton sx={{ pl: 4 }}>
              <ListItemIcon>
                <ScienceIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="GIM" />
            </ListItemButton>
          </List>
        </Collapse>
      </List>
      
      <Divider />
      
      <List>
        <ListItemButton component={Link} to="/settings">
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItemButton>
        
        <ListItemButton component={Link} to="/help">
          <ListItemIcon>
            <HelpIcon />
          </ListItemIcon>
          <ListItemText primary="Help" />
        </ListItemButton>
      </List>
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          boxSizing: 'border-box',
          width: 250,
          backgroundColor: theme.palette.background.paper,
        },
      }}
    >
      {sidebarContent}
    </Drawer>
  );
};

export default Sidebar;

