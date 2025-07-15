import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { BrowserMultiFormatReader } from '@zxing/browser';
import { BarcodeFormat } from '@zxing/library';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [configuration, setConfiguration] = useState({
    itemsPerCase: 10,
    casesPerSscc: 5,
    numberOfSscc: 2,
    useInnerCases: false,
    innerCasesPerCase: 2,
    itemsPerInnerCase: 5,
    companyPrefix: '1234567',
    itemProductCode: '000000',
    caseProductCode: '111111',
    innerCaseProductCode: '222222',
    ssccIndicatorDigit: '0',
    caseIndicatorDigit: '0',
    innerCaseIndicatorDigit: '0',
    itemIndicatorDigit: '0'
  });
  const [configurationId, setConfigurationId] = useState('');
  const [ssccSerials, setSsccSerials] = useState('');
  const [caseSerials, setCaseSerials] = useState('');
  const [innerCaseSerials, setInnerCaseSerials] = useState('');
  const [itemSerials, setItemSerials] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scannerModal, setScannerModal] = useState({ isOpen: false, targetField: '', targetSetter: null });
  const videoRef = useRef(null);
  const codeReader = useRef(null);
  const [isScanning, setIsScanning] = useState(false);

  const handleConfigurationSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/configuration`, {
        items_per_case: configuration.useInnerCases ? 0 : configuration.itemsPerCase,
        cases_per_sscc: configuration.casesPerSscc,
        number_of_sscc: configuration.numberOfSscc,
        use_inner_cases: configuration.useInnerCases,
        inner_cases_per_case: configuration.useInnerCases ? configuration.innerCasesPerCase : 0,
        items_per_inner_case: configuration.useInnerCases ? configuration.itemsPerInnerCase : 0,
        company_prefix: configuration.companyPrefix,
        item_product_code: configuration.itemProductCode,
        case_product_code: configuration.caseProductCode,
        inner_case_product_code: configuration.useInnerCases ? configuration.innerCaseProductCode : '',
        sscc_indicator_digit: configuration.ssccIndicatorDigit,
        case_indicator_digit: configuration.caseIndicatorDigit,
        inner_case_indicator_digit: configuration.useInnerCases ? configuration.innerCaseIndicatorDigit : '',
        item_indicator_digit: configuration.itemIndicatorDigit
      });
      
      setConfigurationId(response.data.id);
      
      // Initialize serial number strings
      setSsccSerials('');
      setCaseSerials('');
      setInnerCaseSerials('');
      setItemSerials('');
      
      setCurrentStep(2);
      setSuccess('Configuration saved successfully!');
    } catch (err) {
      setError('Failed to save configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSerialNumbersSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    // Parse serial numbers from text areas
    const ssccArray = ssccSerials.split('\n').filter(s => s.trim()).map(s => s.trim());
    const caseArray = caseSerials.split('\n').filter(s => s.trim()).map(s => s.trim());
    const innerCaseArray = innerCaseSerials.split('\n').filter(s => s.trim()).map(s => s.trim());
    const itemArray = itemSerials.split('\n').filter(s => s.trim()).map(s => s.trim());
    
    try {
      await axios.post(`${API}/serial-numbers`, {
        configuration_id: configurationId,
        sscc_serial_numbers: ssccArray,
        case_serial_numbers: caseArray,
        inner_case_serial_numbers: innerCaseArray,
        item_serial_numbers: itemArray
      });
      
      setCurrentStep(3);
      setSuccess('Serial numbers saved successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save serial numbers');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateEPCIS = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/generate-epcis`, {
        configuration_id: configurationId,
        read_point: "urn:epc:id:sgln:1234567.00000.0",
        biz_location: "urn:epc:id:sgln:1234567.00001.0"
      }, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'epcis_aggregation.xml');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      setSuccess('EPCIS file generated and downloaded successfully!');
    } catch (err) {
      setError('Failed to generate EPCIS file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setConfiguration({ 
      itemsPerCase: 10,
      casesPerSscc: 5,
      numberOfSscc: 2,
      useInnerCases: false,
      innerCasesPerCase: 2,
      itemsPerInnerCase: 5,
      companyPrefix: '1234567',
      itemProductCode: '000000',
      caseProductCode: '111111',
      innerCaseProductCode: '222222',
      ssccIndicatorDigit: '0',
      caseIndicatorDigit: '0',
      innerCaseIndicatorDigit: '0',
      itemIndicatorDigit: '0'
    });
    setConfigurationId('');
    setSsccSerials('');
    setCaseSerials('');
    setInnerCaseSerials('');
    setItemSerials('');
    setError('');
    setSuccess('');
  };

  // Barcode scanning functions
  const openScanner = (targetField, targetSetter) => {
    setScannerModal({ isOpen: true, targetField, targetSetter });
  };

  const closeScanner = () => {
    setIsScanning(false);
    
    // Stop all video streams
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    // Clean up code reader
    if (codeReader.current) {
      try {
        if (typeof codeReader.current.reset === 'function') {
          codeReader.current.reset();
        }
      } catch (error) {
        console.log('Error stopping scanner:', error);
      }
    }
    
    setScannerModal({ isOpen: false, targetField: '', targetSetter: null });
  };

  const startScanning = async () => {
    try {
      setIsScanning(true);
      
      // Initialize the code reader
      codeReader.current = new BrowserMultiFormatReader();
      
      // Request camera permissions first
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment' // Try to use back camera
        } 
      });
      
      // Set the video stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      // Start scanning
      const result = await codeReader.current.decodeOnceFromVideoDevice(undefined, videoRef.current);
      
      if (result) {
        const scannedData = result.getText();
        handleBarcodeResult(scannedData);
      }
      
    } catch (err) {
      console.error('Error starting scanner:', err);
      setIsScanning(false);
      
      if (err.name === 'NotAllowedError') {
        setError('Camera access denied. Please allow camera permissions and try again.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device');
      } else {
        setError('Failed to start camera scanner: ' + err.message);
      }
    }
  };

  const startContinuousScanning = async () => {
    try {
      setIsScanning(true);
      
      // Initialize the code reader
      codeReader.current = new BrowserMultiFormatReader();
      
      // Request camera permissions and get stream
      const constraints = {
        video: {
          facingMode: 'environment', // Try to use back camera
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      };
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          
          // Wait for video to be ready
          await new Promise((resolve) => {
            videoRef.current.onloadedmetadata = resolve;
          });
          
          // Start scanning
          const scanLoop = async () => {
            if (!scannerModal.isOpen) return;
            
            try {
              const result = await codeReader.current.decodeOnceFromVideoDevice(undefined, videoRef.current);
              if (result) {
                const scannedData = result.getText();
                handleBarcodeResult(scannedData);
                return;
              }
            } catch (scanError) {
              // Continue scanning
            }
            
            // Continue scanning
            setTimeout(scanLoop, 100);
          };
          
          scanLoop();
        }
        
      } catch (permissionError) {
        // Fallback to any available camera
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          
          await new Promise((resolve) => {
            videoRef.current.onloadedmetadata = resolve;
          });
          
          // Start scanning loop
          const scanLoop = async () => {
            if (!scannerModal.isOpen) return;
            
            try {
              const result = await codeReader.current.decodeOnceFromVideoDevice(undefined, videoRef.current);
              if (result) {
                const scannedData = result.getText();
                handleBarcodeResult(scannedData);
                return;
              }
            } catch (scanError) {
              // Continue scanning
            }
            
            setTimeout(scanLoop, 100);
          };
          
          scanLoop();
        }
      }
      
    } catch (err) {
      console.error('Error starting continuous scanner:', err);
      setIsScanning(false);
      
      if (err.name === 'NotAllowedError') {
        setError('Camera access denied. Please allow camera permissions and try again.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device');
      } else {
        setError('Failed to start camera scanner: ' + err.message);
      }
    }
  };

  const handleBarcodeResult = (scannedData) => {
    try {
      // Parse GS1 Data Matrix barcode
      const parsedData = parseGS1Barcode(scannedData);
      
      console.log('Parsed GS1 Data:', parsedData); // Debug log
      
      if (parsedData.serialNumber) {
        // Add the scanned serial number to the current text area
        const currentValue = scannerModal.targetField === 'sscc' ? ssccSerials :
                           scannerModal.targetField === 'case' ? caseSerials :
                           scannerModal.targetField === 'innerCase' ? innerCaseSerials :
                           itemSerials;
        
        const newValue = currentValue ? currentValue + '\n' + parsedData.serialNumber : parsedData.serialNumber;
        scannerModal.targetSetter(newValue);
        
        // Show detailed success message
        let successMessage = `Scanned serial number: ${parsedData.serialNumber}`;
        if (parsedData.gtin) {
          successMessage += `\nGTIN: ${parsedData.gtin}`;
        }
        if (parsedData.batchLot) {
          successMessage += `\nBatch/Lot: ${parsedData.batchLot}`;
        }
        if (parsedData.expirationDate) {
          successMessage += `\nExp Date: ${parsedData.expirationDate}`;
        }
        
        setSuccess(successMessage);
        closeScanner();
      } else {
        setError('Could not extract serial number from barcode');
      }
    } catch (err) {
      console.error('Error parsing barcode:', err);
      setError('Failed to parse barcode data');
    }
  };

  const parseGS1Barcode = (barcodeData) => {
    // GS1 Group Separator character (ASCII 29)
    const GS1_SEPARATOR = '\u001d';
    
    let serialNumber = '';
    let gtin = '';
    let sscc = '';
    let batchLot = '';
    let expirationDate = '';
    
    // Clean the data and split by GS1 separators
    let cleanData = barcodeData;
    
    // Replace GS1 separators with a marker we can split on
    const segments = cleanData.split(GS1_SEPARATOR);
    
    console.log('GS1 Segments:', segments);
    
    // Process each segment
    for (let segment of segments) {
      if (!segment) continue;
      
      // Process this segment
      let remainingData = segment;
      
      while (remainingData.length > 0) {
        // Check for AI 01 (GTIN) - Fixed length 14 digits
        if (remainingData.startsWith('01')) {
          if (remainingData.length >= 16) { // 2 (AI) + 14 (GTIN)
            gtin = remainingData.substring(2, 16);
            remainingData = remainingData.substring(16);
            continue;
          }
        }
        
        // Check for AI 00 (SSCC) - Fixed length 18 digits
        if (remainingData.startsWith('00')) {
          if (remainingData.length >= 20) { // 2 (AI) + 18 (SSCC)
            sscc = remainingData.substring(2, 20);
            remainingData = remainingData.substring(20);
            continue;
          }
        }
        
        // Check for AI 21 (Serial Number) - Variable length (terminated by separator or next AI)
        if (remainingData.startsWith('21')) {
          // For variable length fields, take everything after the AI
          // The separator should have already split this
          serialNumber = remainingData.substring(2);
          remainingData = '';
          continue;
        }
        
        // Check for AI 17 (Expiration Date) - Fixed length 6 digits (YYMMDD)
        if (remainingData.startsWith('17')) {
          if (remainingData.length >= 8) { // 2 (AI) + 6 (Date)
            expirationDate = remainingData.substring(2, 8);
            remainingData = remainingData.substring(8);
            continue;
          }
        }
        
        // Check for AI 10 (Batch/Lot) - Variable length
        if (remainingData.startsWith('10')) {
          // For variable length fields, take everything after the AI
          batchLot = remainingData.substring(2);
          remainingData = '';
          continue;
        }
        
        // Check for AI 11 (Production Date) - Fixed length 6 digits (YYMMDD)
        if (remainingData.startsWith('11')) {
          if (remainingData.length >= 8) { // 2 (AI) + 6 (Date)
            // Skip production date for now, but consume it
            remainingData = remainingData.substring(8);
            continue;
          }
        }
        
        // If we can't parse, skip to next character
        remainingData = remainingData.substring(1);
      }
    }
    
    console.log('GS1 Parsing Debug:', {
      originalData: barcodeData,
      segments: segments,
      gtin,
      serialNumber,
      expirationDate,
      batchLot,
      sscc
    });
    
    // Fallback: if no specific AI found, treat the entire string as a serial number
    if (!serialNumber && !sscc && !gtin) {
      serialNumber = barcodeData.trim();
    }
    
    return {
      serialNumber: serialNumber || sscc,
      gtin,
      sscc,
      batchLot,
      expirationDate,
      rawData: barcodeData
    };
  };

  useEffect(() => {
    if (scannerModal.isOpen) {
      // Small delay to ensure modal is rendered
      setTimeout(() => {
        startContinuousScanning();
      }, 200);
    }
    
    return () => {
      // Cleanup on unmount
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
      
      if (codeReader.current) {
        try {
          if (typeof codeReader.current.reset === 'function') {
            codeReader.current.reset();
          }
        } catch (error) {
          console.log('Cleanup error:', error);
        }
      }
    };
  }, [scannerModal.isOpen]);

  const calculateTotals = () => {
    const totalCases = configuration.casesPerSscc * configuration.numberOfSscc;
    if (configuration.useInnerCases) {
      const totalInnerCases = configuration.innerCasesPerCase * totalCases;
      const totalItems = configuration.itemsPerInnerCase * totalInnerCases;
      return { totalCases, totalInnerCases, totalItems };
    } else {
      const totalItems = configuration.itemsPerCase * totalCases;
      return { totalCases, totalInnerCases: 0, totalItems };
    }
  };

  const renderStep1 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit} className="config-form">
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="casesPerSscc">Cases per SSCC:</label>
            <input
              type="number"
              id="casesPerSscc"
              min="1"
              max="50"
              value={configuration.casesPerSscc}
              onChange={(e) => setConfiguration({...configuration, casesPerSscc: parseInt(e.target.value)})}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="numberOfSscc">Number of SSCCs:</label>
            <input
              type="number"
              id="numberOfSscc"
              min="1"
              max="20"
              value={configuration.numberOfSscc}
              onChange={(e) => setConfiguration({...configuration, numberOfSscc: parseInt(e.target.value)})}
              required
            />
          </div>
        </div>
        
        <div className="inner-case-section">
          <h3>Inner Case Configuration</h3>
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={configuration.useInnerCases}
                onChange={(e) => setConfiguration({...configuration, useInnerCases: e.target.checked})}
              />
              Use Inner Cases (optional intermediate packaging level)
            </label>
            <small className="form-hint">Enable this if you have inner cases between cases and items</small>
          </div>
          
          {configuration.useInnerCases ? (
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="innerCasesPerCase">Inner Cases per Case:</label>
                <input
                  type="number"
                  id="innerCasesPerCase"
                  min="1"
                  max="50"
                  value={configuration.innerCasesPerCase}
                  onChange={(e) => setConfiguration({...configuration, innerCasesPerCase: parseInt(e.target.value)})}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="itemsPerInnerCase">Items per Inner Case:</label>
                <input
                  type="number"
                  id="itemsPerInnerCase"
                  min="1"
                  max="100"
                  value={configuration.itemsPerInnerCase}
                  onChange={(e) => setConfiguration({...configuration, itemsPerInnerCase: parseInt(e.target.value)})}
                  required
                />
              </div>
            </div>
          ) : (
            <div className="form-group">
              <label htmlFor="itemsPerCase">Items per Case (direct):</label>
              <input
                type="number"
                id="itemsPerCase"
                min="1"
                max="100"
                value={configuration.itemsPerCase}
                onChange={(e) => setConfiguration({...configuration, itemsPerCase: parseInt(e.target.value)})}
                required
              />
            </div>
          )}
        </div>
        
        <div className="gs1-section">
          <h3>GS1 Identifier Configuration</h3>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="companyPrefix">Company Prefix:</label>
              <input
                type="text"
                id="companyPrefix"
                value={configuration.companyPrefix}
                onChange={(e) => setConfiguration({...configuration, companyPrefix: e.target.value})}
                placeholder="e.g., 1234567"
                required
              />
              <small className="form-hint">Your GS1 Company Prefix (usually 7-12 digits)</small>
            </div>
            <div className="form-group">
              <label htmlFor="itemProductCode">Item Product Code:</label>
              <input
                type="text"
                id="itemProductCode"
                value={configuration.itemProductCode}
                onChange={(e) => setConfiguration({...configuration, itemProductCode: e.target.value})}
                placeholder="e.g., 000000"
                required
              />
              <small className="form-hint">Product code for individual items (eaches)</small>
            </div>
            <div className="form-group">
              <label htmlFor="caseProductCode">Case Product Code:</label>
              <input
                type="text"
                id="caseProductCode"
                value={configuration.caseProductCode}
                onChange={(e) => setConfiguration({...configuration, caseProductCode: e.target.value})}
                placeholder="e.g., 111111"
                required
              />
              <small className="form-hint">Product code for case containers</small>
            </div>
            {configuration.useInnerCases && (
              <div className="form-group">
                <label htmlFor="innerCaseProductCode">Inner Case Product Code:</label>
                <input
                  type="text"
                  id="innerCaseProductCode"
                  value={configuration.innerCaseProductCode}
                  onChange={(e) => setConfiguration({...configuration, innerCaseProductCode: e.target.value})}
                  placeholder="e.g., 222222"
                  required
                />
                <small className="form-hint">Product code for inner case containers</small>
              </div>
            )}
          </div>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="ssccIndicatorDigit">SSCC Indicator Digit:</label>
              <input
                type="text"
                id="ssccIndicatorDigit"
                maxLength="1"
                value={configuration.ssccIndicatorDigit}
                onChange={(e) => setConfiguration({...configuration, ssccIndicatorDigit: e.target.value})}
                placeholder="0"
                required
              />
              <small className="form-hint">Single digit (0-9) for SSCC containers</small>
            </div>
            <div className="form-group">
              <label htmlFor="caseIndicatorDigit">Case Indicator Digit:</label>
              <input
                type="text"
                id="caseIndicatorDigit"
                maxLength="1"
                value={configuration.caseIndicatorDigit}
                onChange={(e) => setConfiguration({...configuration, caseIndicatorDigit: e.target.value})}
                placeholder="0"
                required
              />
              <small className="form-hint">Single digit (0-9) for case SGTINs</small>
            </div>
            {configuration.useInnerCases && (
              <div className="form-group">
                <label htmlFor="innerCaseIndicatorDigit">Inner Case Indicator Digit:</label>
                <input
                  type="text"
                  id="innerCaseIndicatorDigit"
                  maxLength="1"
                  value={configuration.innerCaseIndicatorDigit}
                  onChange={(e) => setConfiguration({...configuration, innerCaseIndicatorDigit: e.target.value})}
                  placeholder="0"
                  required
                />
                <small className="form-hint">Single digit (0-9) for inner case SGTINs</small>
              </div>
            )}
            <div className="form-group">
              <label htmlFor="itemIndicatorDigit">Item Indicator Digit:</label>
              <input
                type="text"
                id="itemIndicatorDigit"
                maxLength="1"
                value={configuration.itemIndicatorDigit}
                onChange={(e) => setConfiguration({...configuration, itemIndicatorDigit: e.target.value})}
                placeholder="0"
                required
              />
              <small className="form-hint">Single digit (0-9) for item SGTINs</small>
            </div>
          </div>
        </div>
        
        <div className="hierarchy-section">
          <h3>Packaging Hierarchy</h3>
          <div className="hierarchy-visual">
            <div className="hierarchy-level">
              <strong>SSCCs:</strong> {configuration.numberOfSscc}
            </div>
            <div className="hierarchy-arrow">↓</div>
            <div className="hierarchy-level">
              <strong>Cases:</strong> {calculateTotals().totalCases} total
            </div>
            {configuration.useInnerCases && (
              <>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Inner Cases:</strong> {calculateTotals().totalInnerCases} total
                </div>
              </>
            )}
            <div className="hierarchy-arrow">↓</div>
            <div className="hierarchy-level">
              <strong>Items (Eaches):</strong> {calculateTotals().totalItems} total
            </div>
          </div>
        </div>
        
        <div className="summary">
          <h4>GS1 Identifier Examples</h4>
          <p><strong>SSCC:</strong> urn:epc:id:sscc:{configuration.companyPrefix}.{configuration.ssccIndicatorDigit}[sscc_serial]</p>
          <p><strong>Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.caseIndicatorDigit}{configuration.caseProductCode}.[case_serial]</p>
          {configuration.useInnerCases && (
            <p><strong>Inner Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.innerCaseIndicatorDigit}{configuration.innerCaseProductCode}.[inner_case_serial]</p>
          )}
          <p><strong>Item SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.itemIndicatorDigit}{configuration.itemProductCode}.[item_serial]</p>
        </div>
        
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );

  const renderStep2 = () => {
    const totals = calculateTotals();
    
    // Count entered serial numbers
    const ssccCount = ssccSerials.split('\n').filter(s => s.trim()).length;
    const caseCount = caseSerials.split('\n').filter(s => s.trim()).length;
    const innerCaseCount = innerCaseSerials.split('\n').filter(s => s.trim()).length;
    const itemCount = itemSerials.split('\n').filter(s => s.trim()).length;
    
    return (
      <div className="step-container">
        <h2 className="step-title">Step 2: Serial Numbers</h2>
        <form onSubmit={handleSerialNumbersSubmit} className="serial-form">
          
          <div className="serial-section">
            <h3>SSCC Serial Numbers 
              <span className={`counter ${ssccCount === configuration.numberOfSscc ? 'counter-complete' : ''}`}>
                ({ssccCount}/{configuration.numberOfSscc})
              </span>
            </h3>
            <div className="textarea-group">
              <div className="textarea-with-scanner">
                <textarea
                  value={ssccSerials}
                  onChange={(e) => setSsccSerials(e.target.value)}
                  placeholder="Enter SSCC serial numbers, one per line"
                  rows="5"
                  required
                />
                <button 
                  type="button" 
                  className="scan-button"
                  onClick={() => openScanner('sscc', setSsccSerials)}
                  title="Scan barcode"
                >
                  📷
                </button>
              </div>
              <small className="form-hint">Enter {configuration.numberOfSscc} SSCC serial numbers, one per line</small>
            </div>
          </div>

          <div className="serial-section">
            <h3>Case Serial Numbers 
              <span className={`counter ${caseCount === totals.totalCases ? 'counter-complete' : ''}`}>
                ({caseCount}/{totals.totalCases})
              </span>
            </h3>
            <div className="textarea-group">
              <div className="textarea-with-scanner">
                <textarea
                  value={caseSerials}
                  onChange={(e) => setCaseSerials(e.target.value)}
                  placeholder="Enter case serial numbers, one per line"
                  rows="8"
                  required
                />
                <button 
                  type="button" 
                  className="scan-button"
                  onClick={() => openScanner('case', setCaseSerials)}
                  title="Scan barcode"
                >
                  📷
                </button>
              </div>
              <small className="form-hint">Enter {totals.totalCases} case serial numbers, one per line</small>
            </div>
          </div>

          {configuration.useInnerCases && (
            <div className="serial-section">
              <h3>Inner Case Serial Numbers 
                <span className={`counter ${innerCaseCount === totals.totalInnerCases ? 'counter-complete' : ''}`}>
                  ({innerCaseCount}/{totals.totalInnerCases})
                </span>
              </h3>
              <div className="textarea-group">
                <div className="textarea-with-scanner">
                  <textarea
                    value={innerCaseSerials}
                    onChange={(e) => setInnerCaseSerials(e.target.value)}
                    placeholder="Enter inner case serial numbers, one per line"
                    rows="10"
                    required
                  />
                  <button 
                    type="button" 
                    className="scan-button"
                    onClick={() => openScanner('innerCase', setInnerCaseSerials)}
                    title="Scan barcode"
                  >
                    📷
                  </button>
                </div>
                <small className="form-hint">Enter {totals.totalInnerCases} inner case serial numbers, one per line</small>
              </div>
            </div>
          )}

          <div className="serial-section">
            <h3>Item Serial Numbers (Eaches)
              <span className={`counter ${itemCount === totals.totalItems ? 'counter-complete' : ''}`}>
                ({itemCount}/{totals.totalItems})
              </span>
            </h3>
            <div className="textarea-group">
              <div className="textarea-with-scanner">
                <textarea
                  value={itemSerials}
                  onChange={(e) => setItemSerials(e.target.value)}
                  placeholder="Enter item serial numbers, one per line"
                  rows="15"
                  required
                />
                <button 
                  type="button" 
                  className="scan-button"
                  onClick={() => openScanner('item', setItemSerials)}
                  title="Scan barcode"
                >
                  📷
                </button>
              </div>
              <small className="form-hint">Enter {totals.totalItems} item serial numbers, one per line</small>
            </div>
          </div>

          <div className="button-group">
            <button type="button" onClick={() => setCurrentStep(1)} className="btn-secondary">
              Back
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? 'Saving...' : 'Save Serial Numbers'}
            </button>
          </div>
        </form>
      </div>
    );
  };

  const renderStep3 = () => {
    const totals = calculateTotals();
    
    return (
      <div className="step-container">
        <h2 className="step-title">Step 3: Generate EPCIS File</h2>
        <div className="summary-section">
          <h3>Configuration Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <strong>Cases per SSCC:</strong> {configuration.casesPerSscc}
            </div>
            <div className="summary-item">
              <strong>Number of SSCCs:</strong> {configuration.numberOfSscc}
            </div>
            <div className="summary-item">
              <strong>Total Cases:</strong> {totals.totalCases}
            </div>
            {configuration.useInnerCases && (
              <>
                <div className="summary-item">
                  <strong>Inner Cases per Case:</strong> {configuration.innerCasesPerCase}
                </div>
                <div className="summary-item">
                  <strong>Total Inner Cases:</strong> {totals.totalInnerCases}
                </div>
                <div className="summary-item">
                  <strong>Items per Inner Case:</strong> {configuration.itemsPerInnerCase}
                </div>
              </>
            )}
            {!configuration.useInnerCases && (
              <div className="summary-item">
                <strong>Items per Case:</strong> {configuration.itemsPerCase}
              </div>
            )}
            <div className="summary-item">
              <strong>Total Items:</strong> {totals.totalItems}
            </div>
          </div>
          
          <div className="epcis-info">
            <h4>EPCIS File Details</h4>
            <p>The generated file will contain GS1 compliant EPCIS 1.2 XML with commissioning and aggregation events for pharmaceutical serialization.</p>
            <ul>
              <li>Company Prefix: {configuration.companyPrefix}</li>
              <li>Item Product Code: {configuration.itemProductCode}</li>
              <li>Case Product Code: {configuration.caseProductCode}</li>
              {configuration.useInnerCases && (
                <li>Inner Case Product Code: {configuration.innerCaseProductCode}</li>
              )}
              <li>SSCC Indicator: {configuration.ssccIndicatorDigit}</li>
              <li>Case Indicator: {configuration.caseIndicatorDigit}</li>
              {configuration.useInnerCases && (
                <li>Inner Case Indicator: {configuration.innerCaseIndicatorDigit}</li>
              )}
              <li>Item Indicator: {configuration.itemIndicatorDigit}</li>
              <li>Format: EPCIS 1.2 Standard</li>
              <li>Event Types: Commissioning + Aggregation Events</li>
              <li>Hierarchy: {configuration.useInnerCases ? 'SSCC → Cases → Inner Cases → Items' : 'SSCC → Cases → Items'}</li>
              <li>Business Step: Commissioning + Packing</li>
            </ul>
          </div>
        </div>
        
        <div className="button-group">
          <button type="button" onClick={() => setCurrentStep(2)} className="btn-secondary">
            Back
          </button>
          <button onClick={handleGenerateEPCIS} disabled={isLoading} className="btn-primary">
            {isLoading ? 'Generating...' : 'Generate & Download EPCIS'}
          </button>
          <button onClick={handleReset} className="btn-outline">
            Start Over
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <img className="header-logo" src="https://cdn.prod.website-files.com/6154ee5ad4b73423326331fd/66a2bd8c5b618c82f5e30699_rxerp-logo-hero-light.svg"></img>
          <h1>RxERP Aggregator</h1>
          <p>Generate GS1 compliant EPCIS files for pharmaceutical serialization</p>
        </header>

        <div className="progress-bar">
          <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>1</div>
          <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>2</div>
          <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>3</div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Barcode Scanner Modal */}
        {scannerModal.isOpen && (
          <div className="scanner-modal">
            <div className="scanner-overlay" onClick={closeScanner}></div>
            <div className="scanner-content">
              <div className="scanner-header">
                <h3>Scan Barcode</h3>
                <button className="close-button" onClick={closeScanner}>×</button>
              </div>
              <div className="scanner-body">
                <div className="camera-container">
                  <video ref={videoRef} className="scanner-video" autoPlay muted playsInline></video>
                  {isScanning && (
                    <div className="scanning-overlay">
                      <div className="scanning-frame"></div>
                      <p className="scanning-text">Scanning...</p>
                    </div>
                  )}
                </div>
                <div className="scanner-instructions">
                  <p>Position the barcode within the camera view</p>
                  <p>Supported formats: GS1 Data Matrix, QR codes</p>
                  {!isScanning && (
                    <p className="error-text">Camera not started. Please check permissions.</p>
                  )}
                </div>
              </div>
              <div className="scanner-footer">
                <button className="btn-secondary" onClick={closeScanner}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        <main className="main-content">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </main>
      </div>
    </div>
  );
}

export default App;