/**
 * ScandIt Scanner Component for EPCIS Aggregator
 * Handles both single scanning (SparkScan) and batch scanning (MatrixScan)  
 * Optimized for Data Matrix codes only
 */

export class ScandItScanner {
  constructor(licenseKey) {
    this.licenseKey = licenseKey;
    this.isInitialized = false;
    this.currentMode = null; // 'single' or 'batch'
    
    // ScandIt modules will be loaded dynamically
    this.SDCCore = null;
    this.SDCBarcode = null;
    
    // ScandIt instances
    this.context = null;
    this.camera = null;
    this.view = null;
    this.sparkScan = null;
    this.barcodeBatch = null;
  }

  /**
   * Initialize ScandIt SDK with dynamic imports
   */
  async initialize() {
    try {
      console.log('🚀 Initializing ScandIt SDK...');
      
      // Dynamically import ScandIt modules
      console.log('📦 Loading ScandIt modules...');
      this.SDCCore = await import('@scandit/web-datacapture-core');
      this.SDCBarcode = await import('@scandit/web-datacapture-barcode');
      
      console.log('✅ ScandIt modules loaded:', {
        coreLoaded: !!this.SDCCore,
        barcodeLoaded: !!this.SDCBarcode
      });
      
      // Configure ScandIt with license key
      console.log('🔑 Configuring ScandIt with license key...');
      await this.SDCCore.configure({
        licenseKey: this.licenseKey,
        libraryLocation: "https://cdn.jsdelivr.net/npm/@scandit/web-datacapture-core@7/build/",
        moduleLoaders: [this.SDCBarcode.barcodeCaptureLoader()]
      });

      // Create data capture context
      console.log('🎯 Creating data capture context...');
      this.context = await this.SDCCore.DataCaptureContext.create();
      
      // Setup camera with optimized settings
      this.camera = this.SDCCore.Camera.default;
      
      console.log('✅ ScandIt SDK initialized successfully');
      this.isInitialized = true;
      
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize ScandIt:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        coreModule: !!this.SDCCore,
        barcodeModule: !!this.SDCBarcode
      });
      throw new Error(`ScandIt initialization failed: ${error.message}`);
    }
  }

  /**
   * Create SparkScan for single scanning (SSCC, Cases, Inner Cases)
   */
  async initializeSingleScanner(containerElement, onScanCallback) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      console.log('📱 Setting up SparkScan for single scanning...');

      // Configure SparkScan settings for Data Matrix only
      const settings = new this.SDCBarcode.SparkScanSettings();
      settings.enabledSymbologies = [this.SDCBarcode.Symbology.DataMatrix]; // Data Matrix ONLY
      settings.codeDuplicateFilter = 0; // Allow immediate re-scanning
      settings.scanIntention = this.SDCBarcode.ScanIntention.Smart; // Smart scanning intention

      // Create SparkScan instance
      this.sparkScan = await this.SDCBarcode.SparkScan.forSettings(settings);

      // Configure SparkScan view settings
      const viewSettings = new this.SDCBarcode.SparkScanViewSettings();
      viewSettings.defaultScanningMode = this.SDCBarcode.SparkScanScanningModeTarget; // Precision scanning
      viewSettings.soundEnabled = true; // Built-in beep
      viewSettings.hapticEnabled = true; // Built-in haptic feedback
      viewSettings.cameraSwitchButtonVisible = false; // Hide camera switch
      viewSettings.torchButtonVisible = true; // Show torch button

      // Create SparkScan view
      const sparkScanView = await this.SDCBarcode.SparkScanView.withSettingsForContext(
        this.context,
        this.sparkScan,
        viewSettings
      );

      // Setup scan listener
      this.sparkScan.addListener({
        didScan: (sparkScan, session) => {
          const barcode = session.newlyRecognizedBarcodes[0];
          if (barcode && barcode.symbology === this.SDCBarcode.Symbology.DataMatrix) {
            console.log('✅ SparkScan detected Data Matrix:', barcode.data);
            onScanCallback(barcode.data, 'single');
          }
        }
      });

      // Connect to DOM element
      sparkScanView.connectToElement(containerElement);
      
      // Setup camera
      const cameraSettings = this.SDCBarcode.SparkScan.recommendedCameraSettings;
      await this.camera.applySettings(cameraSettings);
      await this.context.setFrameSource(this.camera);

      this.currentMode = 'single';
      console.log('✅ SparkScan ready for Data Matrix scanning');
      
      return sparkScanView;

    } catch (error) {
      console.error('❌ Failed to setup SparkScan:', error);
      throw new Error(`SparkScan setup failed: ${error.message}`);
    }
  }

  /**
   * Create MatrixScan for batch scanning (Items)
   */
  async initializeBatchScanner(containerElement, onScanCallback) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      console.log('📦 Setting up MatrixScan for batch scanning...');

      // Configure batch settings for Data Matrix only
      const settings = new this.SDCBarcode.BarcodeBatchSettings();
      settings.enabledSymbologies = [this.SDCBarcode.Symbology.DataMatrix]; // Data Matrix ONLY

      // Create BarcodeBatch instance
      this.barcodeBatch = await this.SDCBarcode.BarcodeBatch.forContext(this.context, settings);

      // Setup camera
      const cameraSettings = SDCBarcode.BarcodeBatch.recommendedCameraSettings;
      await this.camera.applySettings(cameraSettings);
      await this.context.setFrameSource(this.camera);

      // Create data capture view
      this.view = await SDCCore.DataCaptureView.forContext(this.context);
      this.view.connectToElement(containerElement);

      // Add batch overlay for visual feedback
      const overlay = await SDCBarcode.BarcodeBatchBasicOverlay.withBarcodeBatchForView(
        this.barcodeBatch,
        this.view
      );

      // Configure overlay appearance
      overlay.listener = {
        brushForTrackedBarcode: (overlay, trackedBarcode) => {
          // Green brush for successfully scanned Data Matrix codes
          if (trackedBarcode.barcode.symbology === SDCBarcode.Symbology.DataMatrix) {
            return new SDCCore.Brush(
              SDCCore.Color.fromHex('#00FF00'), // Green fill
              SDCCore.Color.fromHex('#00AA00'), // Darker green stroke
              3 // Stroke width
            );
          }
          return null;
        },
        
        didTapTrackedBarcode: (overlay, trackedBarcode) => {
          // Handle tapped barcodes
          if (trackedBarcode.barcode.symbology === SDCBarcode.Symbology.DataMatrix) {
            console.log('👆 Tapped Data Matrix:', trackedBarcode.barcode.data);
            onScanCallback(trackedBarcode.barcode.data, 'batch');
          }
        }
      };

      // Setup batch listener for automatic feedback
      const feedback = SDCCore.Feedback.defaultFeedback;
      this.barcodeBatch.addListener({
        didUpdateSession: (barcodeBatch, session) => {
          if (session.addedTrackedBarcodes.length > 0) {
            // Emit feedback for new Data Matrix codes
            session.addedTrackedBarcodes.forEach(trackedBarcode => {
              if (trackedBarcode.barcode.symbology === SDCBarcode.Symbology.DataMatrix) {
                feedback.emit();
                console.log('✅ MatrixScan detected Data Matrix:', trackedBarcode.barcode.data);
                onScanCallback(trackedBarcode.barcode.data, 'batch');
              }
            });
          }
        }
      });

      this.currentMode = 'batch';
      console.log('✅ MatrixScan ready for batch Data Matrix scanning');
      
      return this.view;

    } catch (error) {
      console.error('❌ Failed to setup MatrixScan:', error);
      throw new Error(`MatrixScan setup failed: ${error.message}`);
    }
  }

  /**
   * Start scanning
   */
  async startScanning() {
    try {
      if (!this.camera) {
        throw new Error('Camera not initialized');
      }

      await this.camera.switchToDesiredState(SDCCore.FrameSourceState.On);
      
      if (this.sparkScan) {
        // SparkScan handles its own scanning lifecycle
        console.log('📱 SparkScan started');
      } else if (this.barcodeBatch) {
        this.barcodeBatch.isEnabled = true;
        console.log('📦 MatrixScan started');
      }

    } catch (error) {
      console.error('❌ Failed to start scanning:', error);
      throw error;
    }
  }

  /**
   * Stop scanning
   */
  async stopScanning() {
    try {
      if (this.camera) {
        await this.camera.switchToDesiredState(SDCCore.FrameSourceState.Off);
      }

      if (this.sparkScan) {
        // SparkScan stops automatically when camera stops
        console.log('📱 SparkScan stopped');
      } else if (this.barcodeBatch) {
        this.barcodeBatch.isEnabled = false;
        console.log('📦 MatrixScan stopped');
      }

    } catch (error) {
      console.error('❌ Failed to stop scanning:', error);
    }
  }

  /**
   * Cleanup resources
   */
  async dispose() {
    try {
      console.log('🧹 Disposing ScandIt resources...');

      if (this.camera) {
        await this.camera.switchToDesiredState(SDCCore.FrameSourceState.Off);
      }

      if (this.sparkScan) {
        this.sparkScan.removeAllListeners();
        this.sparkScan = null;
      }

      if (this.barcodeBatch) {
        this.barcodeBatch.removeAllListeners();
        this.barcodeBatch = null;
      }

      if (this.view) {
        this.view.dispose();
        this.view = null;
      }

      if (this.context) {
        await this.context.dispose();
        this.context = null;
      }

      this.camera = null;
      this.isInitialized = false;
      this.currentMode = null;

      console.log('✅ ScandIt resources disposed');

    } catch (error) {
      console.error('❌ Failed to dispose ScandIt resources:', error);
    }
  }
}

export default ScandItScanner;