/**
 * Simple ScandIt Scanner - Ground-up implementation
 * Focus on getting basic Data Matrix scanning working
 */

export class SimpleScandItScanner {
  constructor(licenseKey) {
    this.licenseKey = licenseKey;
    this.isInitialized = false;
    this.context = null;
    this.camera = null;
    this.barcodeBatch = null;
    this.view = null;
    this.onScanCallback = null;
    
    // ScandIt modules
    this.SDCCore = null;
    this.SDCBarcode = null;
  }

  async initialize() {
    try {
      console.log('🚀 Initializing Simple ScandIt Scanner...');
      
      // Import ScandIt modules
      this.SDCCore = await import('@scandit/web-datacapture-core');
      this.SDCBarcode = await import('@scandit/web-datacapture-barcode');
      
      // Configure ScandIt
      const libraryLocation = new URL('scandit-sdk/', document.baseURI).toString();
      await this.SDCCore.configure({
        licenseKey: this.licenseKey,
        libraryLocation: libraryLocation,
        moduleLoaders: [this.SDCBarcode.barcodeCaptureLoader()]
      });

      // Create context
      this.context = await this.SDCCore.DataCaptureContext.create();
      
      // Setup camera
      this.camera = this.SDCCore.Camera.default;
      await this.context.setFrameSource(this.camera);
      
      this.isInitialized = true;
      console.log('✅ Simple ScandIt Scanner initialized');
      return true;
      
    } catch (error) {
      console.error('❌ Simple ScandIt initialization failed:', error);
      throw error;
    }
  }

  async createScanner(containerElement, onScanCallback) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      this.onScanCallback = onScanCallback;
      console.log('📦 Creating simple BarcodeCapture scanner...');

      // Create barcode capture settings (simpler than BarcodeBatch)
      const settings = new this.SDCBarcode.BarcodeCaptureSettings();
      settings.enableSymbology(this.SDCBarcode.Symbology.DataMatrix);

      // Create barcode capture
      this.barcodeCapture = await this.SDCBarcode.BarcodeCapture.forContext(this.context, settings);

      // Create view
      this.view = await this.SDCCore.DataCaptureView.forContext(this.context);
      this.view.connectToElement(containerElement);

      // Add overlay
      const overlay = await this.SDCBarcode.BarcodeCaptureOverlay.withBarcodeCaptureForView(
        this.barcodeCapture,
        this.view
      );

      // Setup listener
      this.barcodeCapture.addListener({
        didScan: (barcodeCapture, session) => {
          console.log('📊 Barcode captured!');
          
          session.newlyRecognizedBarcodes.forEach(barcode => {
            console.log('🔍 Detected:', barcode.data, barcode.symbology);
            
            if (barcode.symbology === this.SDCBarcode.Symbology.DataMatrix) {
              console.log('✅ Data Matrix found:', barcode.data);
              if (this.onScanCallback) {
                this.onScanCallback(barcode.data);
              }
            }
          });
        }
      });

      console.log('✅ Simple BarcodeCapture scanner created');
      return true;

    } catch (error) {
      console.error('❌ Failed to create scanner:', error);
      throw error;
    }
  }

  async startScanning() {
    try {
      if (this.barcodeCapture) {
        this.barcodeCapture.isEnabled = true;
        console.log('📦 BarcodeCapture enabled');
      }
      
      if (this.camera) {
        await this.camera.switchToDesiredState(this.SDCCore.FrameSourceState.On);
        console.log('📷 Camera started');
      }
    } catch (error) {
      console.error('❌ Failed to start scanning:', error);
    }
  }

  async stopScanning() {
    try {
      if (this.barcodeBatch) {
        this.barcodeBatch.isEnabled = false;
      }
      
      if (this.camera) {
        await this.camera.switchToDesiredState(this.SDCCore.FrameSourceState.Off);
      }
      
      console.log('🛑 Scanner stopped');
    } catch (error) {
      console.error('❌ Failed to stop scanning:', error);
    }
  }

  dispose() {
    try {
      if (this.barcodeBatch) {
        this.barcodeBatch.removeAllListeners();
      }
      
      if (this.view) {
        this.view.dispose();
      }
      
      if (this.context) {
        this.context.dispose();
      }
      
      this.isInitialized = false;
      console.log('🧹 Scanner disposed');
    } catch (error) {
      console.error('❌ Failed to dispose:', error);
    }
  }
}

export default SimpleScandItScanner;