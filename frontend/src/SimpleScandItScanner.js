/**
 * Ultra Simple ScandIt Scanner - Using Direct SDK Approach
 * Based on official ScandIt documentation pattern
 */

export class SimpleScandItScanner {
  constructor(licenseKey) {
    this.licenseKey = licenseKey;
    this.scanner = null;
    this.onScanCallback = null;
  }

  async createScanner(containerElement, onScanCallback) {
    try {
      this.onScanCallback = onScanCallback;

      // Import ScandIt modules
      const SDCCore = await import('@scandit/web-datacapture-core');
      const SDCBarcode = await import('@scandit/web-datacapture-barcode');
      
      // Configure ScandIt 
      const libraryLocation = new URL('scandit-sdk/', document.baseURI).toString();
      await SDCCore.configure({
        licenseKey: this.licenseKey,
        libraryLocation: libraryLocation,
        moduleLoaders: [SDCBarcode.barcodeCaptureLoader()]
      });

      // Create context
      const context = await SDCCore.DataCaptureContext.create();
      
      // Create settings - only Data Matrix
      const settings = new SDCBarcode.BarcodeCaptureSettings();
      settings.enableSymbology(SDCBarcode.Symbology.DataMatrix);
      
      // Create BarcodeCapture
      const barcodeCapture = await SDCBarcode.BarcodeCapture.forContext(context, settings);
      
      // Add capture mode to context
      context.addMode(barcodeCapture);
      
      // Setup camera
      const camera = SDCCore.Camera.default;
      await context.setFrameSource(camera);
      
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
          // Check for the correct property structure (singular barcode)
          if (session && session._newlyRecognizedBarcode) {
            const barcode = session._newlyRecognizedBarcode;
            
            // Debouncing: prevent duplicate scans within 2 seconds of same data
            const now = Date.now();
            const isNewScan = (barcode._data !== lastScanData) || (now - lastScanTime > 2000);
            
            if (isNewScan && this.onScanCallback) {
              lastScanTime = now;
              lastScanData = barcode._data;
              this.onScanCallback(barcode._data);
            }
          }
        }
      });

      // Store references
      this.scanner = { barcodeCapture, camera, view, context };
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

      // Enable capture and start camera
      await this.scanner.barcodeCapture.setEnabled(true);
      
      const SDCCore = await import('@scandit/web-datacapture-core');
      await this.scanner.camera.switchToDesiredState(SDCCore.FrameSourceState.On);
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