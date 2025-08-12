import React from 'react';
import { Box, Typography } from '@mui/material';
import LanIcon from '@mui/icons-material/Lan';
import LanOutlinedIcon from '@mui/icons-material/LanOutlined';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SignalWifi0BarIcon from '@mui/icons-material/SignalWifi0Bar';
import SignalWifi1BarIcon from '@mui/icons-material/SignalWifi1Bar';
import SignalWifi2BarIcon from '@mui/icons-material/SignalWifi2Bar';
import SignalWifi3BarIcon from '@mui/icons-material/SignalWifi3Bar';
import SignalWifi4BarIcon from '@mui/icons-material/SignalWifi4Bar';

const wifiSignalIcons = [
  <SignalWifi0BarIcon color="disabled" />,
  <SignalWifi1BarIcon color="error" />,
  <SignalWifi2BarIcon color="warning" />,
  <SignalWifi3BarIcon color="info" />,
  <SignalWifi4BarIcon color="success" />,
];

function WifiStatus({ connected, level }) {
  if (!connected) {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <WifiOffIcon color="disabled" />
        <Typography variant="body2" color="textSecondary">Wi-Fi 未接続</Typography>
      </Box>
    );
  }

  // levelは0〜4の想定
  const icon = wifiSignalIcons[Math.min(Math.max(level, 0), 4)];

  return (
    <Box display="flex" alignItems="center" gap={1}>
      {icon}
      <Typography variant="body2" color="textPrimary">Wi-Fi 接続中 (電波レベル: {level})</Typography>
    </Box>
  );
}

function LanStatus({ connected }) {
  return (
    <Box display="flex" alignItems="center" gap={1}>
      {connected ? <LanIcon color="primary" /> : <LanOutlinedIcon color="disabled" />}
      <Typography variant="body2" color={connected ? 'textPrimary' : 'textSecondary'}>
        有線LAN {connected ? '接続中' : '未接続'}
      </Typography>
    </Box>
  );
}

export default function NetworkStatus({ wifi, lan }) {
  // wifi = { connected: boolean, level: 0-4 }
  // lan = { connected: boolean }
  return (
    <Box display="flex" flexDirection="column" gap={2} padding={2} border={1} borderRadius={2} borderColor="grey.300" width={250}>
      <WifiStatus connected={wifi.connected} level={wifi.level} />
      <LanStatus connected={lan.connected} />
    </Box>
  );
}

