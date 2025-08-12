import React from 'react';
import NetworkStatus from './components/NetworkStatus';

export default function App() {
  // 仮のデータ（後でバックエンドやAPIから取得する想定）
  const wifi = { connected: true, level: 3 };
  const lan = { connected: false };

  return (
    <div style={{ padding: 20 }}>
      <NetworkStatus wifi={wifi} lan={lan} />
    </div>
  );
}

