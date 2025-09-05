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
      console.log('🚀 Creating Ultra Simple ScandIt Scanner...');
      this.onScanCallback = onScanCallback;

      // Import ScandIt modules
      const SDCCore = await import('@scandit/web-datacapture-core');
      const SDCBarcode = await import('@scandit/web-datacapture-barcode');
      
      // Configure ScandIt with local files (back to working approach)
      console.log('📁 Using local library files...');
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
      
      // Setup camera AFTER BarcodeCapture is created
      const camera = SDCCore.Camera.default;
      await context.setFrameSource(camera);
      
      // Create view
      const view = await SDCCore.DataCaptureView.forContext(context);
      view.connectToElement(containerElement);
      
      // Create overlay
      const overlay = await SDCBarcode.BarcodeCaptureOverlay.withBarcodeCaptureForView(barcodeCapture, view);
      
      // Add listener
      barcodeCapture.addListener({
        didScan: (barcodeCapture, session) => {
          console.log('📊 Ultra Simple - Barcode scanned!');
          
          session.newlyRecognizedBarcodes.forEach(barcode => {
            console.log('🔍 Ultra Simple - Detected:', barcode.data, barcode.symbology);
            
            if (this.onScanCallback) {
              this.onScanCallback(barcode.data);
            }
          });
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

      console.log('🎬 Ultra Simple - Starting with proper context...');
      
      // Enable capture first
      console.log('📦 Enabling BarcodeCapture...');
      this.scanner.barcodeCapture.isEnabled = true;
      console.log('✅ BarcodeCapture enabled:', this.scanner.barcodeCapture.isEnabled);
      
      // Debug context state before starting camera
      console.log('📷 Debugging context state...');
      console.log('Context:', this.scanner.context);
      console.log('Camera:', this.scanner.camera);
      console.log('BarcodeCapture:', this.scanner.barcodeCapture);
      
      // Try different camera start approach
      console.log('📷 Starting camera with explicit state check...');
      const SDCCore = await import('@scandit/web-datacapture-core');
      
      // Check current camera state first
      console.log('Current camera state:', this.scanner.camera.currentState);
      console.log('Desired camera state would be:', SDCCore.FrameSourceState.On);
      
      // Try to start camera with error isolation
      try {
        await this.scanner.camera.switchToDesiredState(SDCCore.FrameSourceState.On);
        console.log('✅ Camera started successfully!');
      } catch (cameraError) {
        console.error('❌ Camera start failed:', cameraError);
        console.error('Camera error stack:', cameraError.stack);
        
        // Try alternative - just enable capture without camera start
        console.log('🔄 Trying capture-only mode...');
        throw cameraError;
      }
      
      console.log('🚀 Ultra Simple - Scanner fully operational!');
    } catch (error) {
      console.error('❌ Ultra Simple - Failed to start:', error);
      console.error('Error details:', error.stack);
      throw error;
    }
  }

  async stopScanning() {
    try {
      if (this.scanner) {
        this.scanner.barcodeCapture.isEnabled = false;
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