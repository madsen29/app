/**
 * Ultra Simple ScandIt Scanner - Using Direct SDK Approach
 * Based on official ScandIt documentation pattern
 */

export class SimpleScandItScanner {
  constructor(licenseKey) {
    console.log('🔑 Scanner constructor - License key length:', licenseKey?.length);
    console.log('🔑 Scanner constructor - License key preview:', licenseKey?.substring(0, 50) + '...');
    this.licenseKey = licenseKey;
    this.scanner = null;
    this.onScanCallback = null;
  }

  async createScanner(containerElement, onScanCallback) {
    try {
      console.log('🚀 Creating Ultra Simple ScandIt Scanner...');
      this.onScanCallback = onScanCallback;

      // Import ScandIt modules
      const SDCCore = await import('@scandit/web-datacapture-core');
      const SDCBarcode = await import('@scandit/web-datacapture-barcode');
      
      // Configure ScandIt with local files (back to working approach)
      console.log('📁 Using local library files...');
      console.log('🌐 Current domain:', window.location.hostname);
      console.log('🔑 License key preview:', this.licenseKey.substring(0, 30) + '...' + this.licenseKey.substring(this.licenseKey.length - 10));
      
      const libraryLocation = new URL('scandit-sdk/', document.baseURI).toString();
      await SDCCore.configure({
        licenseKey: this.licenseKey,
        libraryLocation: libraryLocation,
        moduleLoaders: [SDCBarcode.barcodeCaptureLoader()]
      });

      console.log('✅ ScandIt configured');

      // Create context
      const context = await SDCCore.DataCaptureContext.create();
      
      // Create settings - only Data Matrix
      const settings = new SDCBarcode.BarcodeCaptureSettings();
      settings.enableSymbology(SDCBarcode.Symbology.DataMatrix);
      
      // Create BarcodeCapture
      const barcodeCapture = await SDCBarcode.BarcodeCapture.forContext(context, settings);
      
      // CRITICAL: Add capture mode to context (this was the missing step!)
      context.addMode(barcodeCapture);
      console.log('✅ BarcodeCapture mode added to context');
      
      // Setup camera AFTER BarcodeCapture is created (but don't start it yet)
      const camera = SDCCore.Camera.default;
      await context.setFrameSource(camera);
      console.log('📷 Camera configured as frame source (not started yet)');
      
      // Create view
      const view = await SDCCore.DataCaptureView.forContext(context);
      view.connectToElement(containerElement);
      
      // Create overlay
      const overlay = await SDCBarcode.BarcodeCaptureOverlay.withBarcodeCaptureForView(barcodeCapture, view);
      
      // Add listener with proper error checking and debouncing
      let lastScanTime = 0;
      let lastScanData = '';
      
      barcodeCapture.addListener({
        didScan: (barcodeCapture, session) => {
          console.log('📊 Ultra Simple - Barcode scanned!');
          
          // Check for the correct property structure (singular barcode)
          if (session && session._newlyRecognizedBarcode) {
            const barcode = session._newlyRecognizedBarcode;
            console.log('🔍 Ultra Simple - Detected:', barcode._data, barcode._symbology);
            
            // Debouncing: prevent duplicate scans within 2 seconds of same data
            const now = Date.now();
            const isNewScan = (barcode._data !== lastScanData) || (now - lastScanTime > 2000);
            
            if (isNewScan && this.onScanCallback) {
              console.log('✅ Processing new scan:', barcode._data);
              lastScanTime = now;
              lastScanData = barcode._data;
              this.onScanCallback(barcode._data);
            } else {
              console.log('⏭️ Skipping duplicate scan:', barcode._data);
            }
          } else {
            console.log('⚠️ No barcode in session:', session);
          }
        }
      });

      // Store references
      this.scanner = { barcodeCapture, camera, view, context };
      
      console.log('✅ Ultra Simple Scanner created');
      return true;

    } catch (error) {
      console.error('❌ Ultra Simple Scanner creation failed:', error);
      throw error;
    }
  }

  async startScanning() {
    try {
      if (!this.scanner) {
        throw new Error('Scanner not created');
      }

      console.log('🎬 Ultra Simple - Starting camera AND enabling capture...');
      
      // Enable capture first using proper API method
      console.log('📦 Enabling BarcodeCapture...');
      await this.scanner.barcodeCapture.setEnabled(true);
      console.log('✅ BarcodeCapture enabled:', this.scanner.barcodeCapture.isEnabled());
      
      // Now start camera for the first time
      console.log('📷 Starting camera for the first time...');
      const SDCCore = await import('@scandit/web-datacapture-core');
      await this.scanner.camera.switchToDesiredState(SDCCore.FrameSourceState.On);
      console.log('✅ Camera started - ready to scan!');
      
      console.log('🚀 Ultra Simple - Scanner fully operational!');
    } catch (error) {
      console.error('❌ Ultra Simple - Failed to start:', error);
      throw error;
    }
  }

  async stopScanning() {
    try {
      if (this.scanner) {
        await this.scanner.barcodeCapture.setEnabled(false);
        const SDCCore = await import('@scandit/web-datacapture-core');
        await this.scanner.camera.switchToDesiredState(SDCCore.FrameSourceState.Off);
        console.log('🛑 Ultra Simple - Scanner stopped');
      }
    } catch (error) {
      console.error('❌ Ultra Simple - Failed to stop:', error);
    }
  }

  dispose() {
    try {
      if (this.scanner) {
        this.scanner.barcodeCapture.removeAllListeners();
        this.scanner.view.dispose();
        this.scanner.context.dispose();
        this.scanner = null;
      }
      console.log('🧹 Ultra Simple - Scanner disposed');
    } catch (error) {
      console.error('❌ Ultra Simple - Failed to dispose:', error);
    }
  }
}

export default SimpleScandItScanner;