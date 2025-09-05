import React, { useRef, useEffect, useState } from 'react';
import SimpleScandItScanner from './SimpleScandItScanner';

const SCANDIT_LICENSE_KEY = "Avq2K9OBRx04MGjA0PBXZNg0GJdPLM/Tfykv+wm9WZBVMtoG93WJHfBxpgo7WGNWmHhHRFtEYJpecdnrBgWsLAkdP5ZlYq63v1+63fVPf0KUV3PNwWq1+VlGD4D4XeZCZVBLaapqykHhca2fSWOu1WElRQo0XGK91WeblTlU53qTM7MK8hbiYPACkBWcGhbbFuBvDnuTCGVyLUjoVKZOVi77ChaJYMUb53gt+YWWf5ZyO8WYr+zkgXcUkN7VFtqzuvSZhKQAz9R9FVTqSg5yfS3LmMNk0EtcpOurlgxKtIkZA2zB0hk+AC73W+clFYW0hUivDlIa+3FmYA2YUaUurvXm8FdCNUJoGDQC3le7JX0T2Fxem9G/yIuVV1qQwDHVgGXon0DbBde2jCy28YlqypdViFKseHq4yVWCwxno8/rcGVzj6M3By/ZCy72aQifK1qi/4/FYBlNsyW8Q2XZKtn9EZns8B6vIMcn25WpUvyiAL9PbkiaX2TM+/9a1peyw3zytVg26fyuxcbKNdkDvlFZA/TIuEiQqltkohZuxmGfwGojeT6U2eGWdoGiX8Z2CVkm00JNU302QKkSxvf0F/igdZhZW9HDJQfXSFX8zStGz/jf09CAND+EWlJj7qEO3Pkmi/n3o+ZDnjdiT9NYH3InzoeoLLBsxkZi1FObPf+FtSgNmytMcJWERiKUegF1nQJLyKU3pWoo6OqNWXiV7BjQsMukyW8G+Ti0+rPtmKnR/cA2Vjx4rQxRx1ukltI2tMMHteVzVYXa9BkuGu0b4eWQAH4EB4GarCgkK30aOx6nMB+yDioH+aeZxBBK+F7tu7N3CibuyddHe6ncCSpSBjG/0O3n2mylP6zn80L/z";

function ScannerTest() {
  const scannerContainerRef = useRef(null);
  const scannerRef = useRef(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scannedCodes, setScannedCodes] = useState([]);
  const [error, setError] = useState('');

  const handleScan = (data) => {
    console.log('🎯 Scanned:', data);
    setScannedCodes(prev => [...prev, { data, timestamp: new Date().toLocaleTimeString() }]);
    
    // Haptic feedback
    if (navigator.vibrate) {
      navigator.vibrate(200);
    }
  };

  const startScanning = async () => {
    try {
      setError('');
      console.log('▶️ Starting scanner test...');
      
      if (!scannerRef.current) {
        scannerRef.current = new SimpleScandItScanner(SCANDIT_LICENSE_KEY);
      }

      await scannerRef.current.createScanner(scannerContainerRef.current, handleScan);
      await scannerRef.current.startScanning();
      
      setIsScanning(true);
      console.log('✅ Scanner test started');
      
    } catch (err) {
      console.error('❌ Scanner test failed:', err);
      setError(err.message);
    }
  };

  const stopScanning = async () => {
    try {
      if (scannerRef.current) {
        await scannerRef.current.stopScanning();
        setIsScanning(false);
        console.log('⏹️ Scanner test stopped');
      }
    } catch (err) {
      console.error('❌ Failed to stop scanner:', err);
    }
  };

  useEffect(() => {
    return () => {
      if (scannerRef.current) {
        scannerRef.current.dispose();
      }
    };
  }, []);

  return (
    <div className="scanner-test">
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">ScandIt Scanner Test</h1>
        
        <div className="mb-4">
          <button
            onClick={isScanning ? stopScanning : startScanning}
            className={`px-4 py-2 rounded font-medium ${
              isScanning 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {isScanning ? 'Stop Scanner' : 'Start Scanner'}
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div 
          ref={scannerContainerRef}
          className="scanner-container bg-black rounded-lg"
          style={{ width: '100%', height: '400px' }}
        />

        <div className="mt-4">
          <h2 className="text-lg font-semibold mb-2">Scanned Codes ({scannedCodes.length})</h2>
          <div className="max-h-40 overflow-y-auto">
            {scannedCodes.map((scan, index) => (
              <div key={index} className="bg-gray-100 p-2 rounded mb-1">
                <div className="font-mono text-sm">{scan.data}</div>
                <div className="text-xs text-gray-500">{scan.timestamp}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ScannerTest;