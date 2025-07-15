import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { BrowserMultiFormatReader } from '@zxing/browser';
import { BarcodeFormat } from '@zxing/library';
import { FiCamera, FiChevronRight } from 'react-icons/fi';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [configuration, setConfiguration] = useState({
    itemsPerCase: 10,
    casesPerSscc: 5,
    numberOfSscc: 1,
    useInnerCases: false,
    innerCasesPerCase: 2,
    itemsPerInnerCase: 5,
    companyPrefix: '0345802',
    productCode: '46653',
    lotNumber: '',
    expirationDate: '',
    ssccExtensionDigit: '0',
    caseIndicatorDigit: '0',
    innerCaseIndicatorDigit: '0',
    itemIndicatorDigit: '0',
    // EPCClass data
    productNdc: '',
    packageNdc: '',
    regulatedProductName: '',
    manufacturerName: '',
    dosageFormType: '',
    strengthDescription: '',
    netContentDescription: ''
  });
  const [configurationId, setConfigurationId] = useState('');
  
  // New hierarchical serial number collection state
  const [hierarchicalSerials, setHierarchicalSerials] = useState([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [serialCollectionStep, setSerialCollectionStep] = useState({
    ssccIndex: 0,
    caseIndex: 0,
    innerCaseIndex: 0,
    itemIndex: 0,
    currentLevel: 'sscc', // 'sscc', 'case', 'innerCase', 'item'
    currentSerial: '',
    isComplete: false
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isToastExiting, setIsToastExiting] = useState(false);
  const [scannerModal, setScannerModal] = useState({ isOpen: false, targetField: '', targetSetter: null });
  const [fdaModal, setFdaModal] = useState({ isOpen: false, searchResults: [], isLoading: false });
  const videoRef = useRef(null);
  const codeReader = useRef(null);
  const [isScanning, setIsScanning] = useState(false);

  // Auto-dismiss toast after 4 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        dismissToast();
      }, 4000);
      
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  const dismissToast = () => {
    setIsToastExiting(true);
    setTimeout(() => {
      setError('');
      setSuccess('');
      setIsToastExiting(false);
    }, 300); // Match animation duration
  };

  const scrollToTop = () => {
    // Small delay to ensure the new step content is rendered
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
  };

  const handleConfigurationSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/configuration`, {
        items_per_case: configuration.casesPerSscc === 0 ? configuration.itemsPerCase : (configuration.useInnerCases ? 0 : configuration.itemsPerCase),
        cases_per_sscc: configuration.casesPerSscc,
        number_of_sscc: configuration.numberOfSscc,
        use_inner_cases: configuration.casesPerSscc === 0 ? false : configuration.useInnerCases,
        inner_cases_per_case: configuration.useInnerCases && configuration.casesPerSscc > 0 ? configuration.innerCasesPerCase : 0,
        items_per_inner_case: configuration.useInnerCases && configuration.casesPerSscc > 0 ? configuration.itemsPerInnerCase : 0,
        company_prefix: configuration.companyPrefix,
        item_product_code: configuration.productCode,
        case_product_code: configuration.productCode,
        inner_case_product_code: configuration.useInnerCases && configuration.casesPerSscc > 0 ? configuration.productCode : '',
        lot_number: configuration.lotNumber,
        expiration_date: configuration.expirationDate,
        sscc_indicator_digit: configuration.ssccExtensionDigit,
        case_indicator_digit: configuration.caseIndicatorDigit,
        inner_case_indicator_digit: configuration.useInnerCases && configuration.casesPerSscc > 0 ? configuration.innerCaseIndicatorDigit : '',
        item_indicator_digit: configuration.itemIndicatorDigit,
        // EPCClass data
        product_ndc: configuration.productNdc,
        package_ndc: configuration.packageNdc,
        regulated_product_name: configuration.regulatedProductName,
        manufacturer_name: configuration.manufacturerName,
        dosage_form_type: configuration.dosageFormType,
        strength_description: configuration.strengthDescription,
        net_content_description: configuration.netContentDescription
      });
      
      setConfigurationId(response.data.id);
      
      // Initialize serial number strings
      setSsccSerials('');
      setCaseSerials('');
      setInnerCaseSerials('');
      setItemSerials('');
      
      setCurrentStep(2);
      setSuccess('Configuration saved successfully!');
      scrollToTop();
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
      scrollToTop();
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

  const handleStepClick = (step) => {
    if (step < currentStep) {
      setCurrentStep(step);
      scrollToTop();
      setError('');
      setSuccess('');
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setConfiguration({ 
      itemsPerCase: 10,
      casesPerSscc: 5,
      numberOfSscc: 1,
      useInnerCases: false,
      innerCasesPerCase: 2,
      itemsPerInnerCase: 5,
      companyPrefix: '0345802',
      productCode: '46653',
      lotNumber: '',
      expirationDate: '',
      ssccExtensionDigit: '0',
      caseIndicatorDigit: '0',
      innerCaseIndicatorDigit: '0',
      itemIndicatorDigit: '0',
      // EPCClass data
      productNdc: '',
      packageNdc: '',
      regulatedProductName: '',
      manufacturerName: '',
      dosageFormType: '',
      strengthDescription: '',
      netContentDescription: ''
    });
    setConfigurationId('');
    setSsccSerials('');
    setCaseSerials('');
    setInnerCaseSerials('');
    setItemSerials('');
    setError('');
    setSuccess('');
    scrollToTop();
  };

  const dismissAlert = (type) => {
    dismissToast();
  };

  // Duplicate validation functions
  const validateSerialNumbers = (value, fieldName) => {
    const lines = value.split('\n');
    const serialNumbers = lines.map(line => line.trim()).filter(line => line.length > 0);
    
    // Check for duplicates
    const duplicates = [];
    const seen = new Set();
    
    for (const serial of serialNumbers) {
      if (seen.has(serial)) {
        duplicates.push(serial);
      } else {
        seen.add(serial);
      }
    }
    
    if (duplicates.length > 0) {
      setError(`Duplicate serial numbers found in ${fieldName}: ${duplicates.join(', ')}`);
      // Remove duplicates and return clean value
      const uniqueSerials = [...new Set(serialNumbers)];
      return uniqueSerials.join('\n');
    }
    
    return value;
  };

  const handleSsccSerialsChange = (e) => {
    const validatedValue = validateSerialNumbers(e.target.value, 'SSCC Serial Numbers');
    setSsccSerials(validatedValue);
  };

  const handleCaseSerialsChange = (e) => {
    const validatedValue = validateSerialNumbers(e.target.value, 'Case Serial Numbers');
    setCaseSerials(validatedValue);
  };

  const handleInnerCaseSerialsChange = (e) => {
    const validatedValue = validateSerialNumbers(e.target.value, 'Inner Case Serial Numbers');
    setInnerCaseSerials(validatedValue);
  };

  const handleItemSerialsChange = (e) => {
    const validatedValue = validateSerialNumbers(e.target.value, 'Item Serial Numbers');
    setItemSerials(validatedValue);
  };

  // Package NDC formatting functions
  const formatPackageNdc = (ndc) => {
    if (!ndc) return '';
    
    // Remove any existing hyphens
    const cleanNdc = ndc.replace(/-/g, '');
    
    // Format as 5-4-2 if we have enough digits
    if (cleanNdc.length >= 11) {
      return `${cleanNdc.slice(0, 5)}-${cleanNdc.slice(5, 9)}-${cleanNdc.slice(9, 11)}`;
    } else if (cleanNdc.length >= 9) {
      return `${cleanNdc.slice(0, 5)}-${cleanNdc.slice(5, 9)}-${cleanNdc.slice(9)}`;
    } else if (cleanNdc.length >= 5) {
      return `${cleanNdc.slice(0, 5)}-${cleanNdc.slice(5)}`;
    } else {
      return cleanNdc;
    }
  };

  const handlePackageNdcChange = (e) => {
    let value = e.target.value;
    
    // Remove any non-numeric characters except hyphens
    value = value.replace(/[^0-9-]/g, '');
    
    // Remove hyphens for storage (we'll add them back for display)
    const cleanValue = value.replace(/-/g, '');
    
    // Limit to 11 digits
    if (cleanValue.length <= 11) {
      setConfiguration({...configuration, packageNdc: cleanValue});
    }
  };

  // FDA API functions
  const searchFdaApi = async (ndc) => {
    setFdaModal({ ...fdaModal, isLoading: true });
    
    try {
      // Pass exactly what is entered into the field to the FDA API
      console.log('Searching FDA API with NDC:', ndc);
      
      const response = await fetch(`https://api.fda.gov/drug/ndc.json?search=product_ndc:"${ndc}"&limit=1`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        const product = data.results[0];
        
        // Create packaging options from the product data
        const packagingOptions = [];
        
        if (product.packaging && product.packaging.length > 0) {
          product.packaging.forEach(pkg => {
            packagingOptions.push({
              ...product,
              selectedPackaging: pkg,
              packageNdc: pkg.package_ndc,
              packageDescription: pkg.description,
              productNdc: ndc // Store the original input
            });
          });
        } else {
          // If no packaging info, add the product itself
          packagingOptions.push({
            ...product,
            selectedPackaging: null,
            packageNdc: product.product_ndc,
            packageDescription: 'No packaging information available',
            productNdc: ndc // Store the original input
          });
        }
        
        setFdaModal({
          isOpen: true,
          searchResults: packagingOptions,
          isLoading: false
        });
      } else {
        setError(`No products found for NDC: ${ndc}`);
        setFdaModal({ ...fdaModal, isLoading: false });
      }
    } catch (error) {
      console.error('FDA API Error:', error);
      setError('Failed to search FDA API: ' + error.message);
      setFdaModal({ ...fdaModal, isLoading: false });
    }
  };

  const handleFdaSearch = () => {
    if (configuration.productNdc) {
      searchFdaApi(configuration.productNdc);
    } else {
      setError('Please enter a Product NDC number');
    }
  };

  const selectFdaProduct = (productOption) => {
    // Extract Product Code from Package NDC by combining last 2 sections
    // Example: "45802-466-35" -> last 2 sections are "466-35" -> "46635"
    const packageNdc = productOption.packageNdc;
    const ndcParts = packageNdc.split('-');
    
    // Combine the last 2 sections (product code + package code)
    let productCodeForGS1 = '';
    if (ndcParts.length >= 3) {
      // Take the last 2 sections and combine them
      const productSection = ndcParts[ndcParts.length - 2]; // Second to last section
      const packageSection = ndcParts[ndcParts.length - 1]; // Last section
      productCodeForGS1 = productSection + packageSection;
    } else {
      // Fallback if NDC format is unexpected
      productCodeForGS1 = packageNdc.replace(/-/g, '').slice(5);
    }
    
    // Extract Company Prefix from first section of Package NDC
    // Example: "0574-0820-10" -> first section is "0574" -> prepend "03" -> "030574"
    let companyPrefix = '';
    if (ndcParts.length >= 1) {
      // Take the first section and prepend "03"
      const firstSection = ndcParts[0];
      companyPrefix = "03" + firstSection;
    } else {
      // Fallback if NDC format is unexpected
      const rawPackageNdc = packageNdc.replace(/-/g, '');
      companyPrefix = "03" + rawPackageNdc.slice(0, 5);
    }
    
    // For Package NDC storage, ensure it's properly formatted as 11 digits
    const rawPackageNdc = packageNdc.replace(/-/g, '');
    let selectedPackageNdc;
    
    if (rawPackageNdc.length === 10) {
      // Convert 10-digit to 11-digit by adding leading zero to product code
      // Format: LLLLL-PPP-KK becomes LLLLL-0PPP-KK
      const labelerCode = rawPackageNdc.slice(0, 5);
      const productCode = rawPackageNdc.slice(5, 8);
      const packageCode = rawPackageNdc.slice(8, 10);
      selectedPackageNdc = labelerCode + '0' + productCode + packageCode;
    } else if (rawPackageNdc.length === 11) {
      // Already 11 digits, use as-is
      selectedPackageNdc = rawPackageNdc;
    } else {
      // Invalid length, use as-is but might cause issues
      selectedPackageNdc = rawPackageNdc;
    }
    
    setConfiguration({
      ...configuration,
      productNdc: productOption.productNdc, // Store the 10-digit product NDC
      packageNdc: selectedPackageNdc, // Store the 11-digit package NDC without hyphens
      companyPrefix: companyPrefix, // Company prefix from first section of Package NDC
      productCode: productCodeForGS1, // Product code from last 2 sections of Package NDC
      regulatedProductName: productOption.brand_name || productOption.generic_name || '',
      manufacturerName: productOption.labeler_name || '',
      dosageFormType: productOption.dosage_form || '',
      strengthDescription: productOption.active_ingredients?.map(ing => 
        `${ing.name} ${ing.strength}`
      ).join(', ') || '',
      netContentDescription: productOption.packageDescription || ''
    });
    
    setFdaModal({ isOpen: false, searchResults: [], isLoading: false });
    setSuccess(`Product loaded: ${productOption.packageDescription}. Company Prefix: ${companyPrefix}, Product Code: ${productCodeForGS1}`);
  };

  const closeFdaModal = () => {
    setFdaModal({ isOpen: false, searchResults: [], isLoading: false });
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
        // Add the scanned serial number to the current text area with validation
        const currentValue = scannerModal.targetField === 'sscc' ? ssccSerials :
                           scannerModal.targetField === 'case' ? caseSerials :
                           scannerModal.targetField === 'innerCase' ? innerCaseSerials :
                           itemSerials;
        
        const newValue = currentValue ? currentValue + '\n' + parsedData.serialNumber : parsedData.serialNumber;
        
        // Use validation functions based on target field
        let validatedValue;
        if (scannerModal.targetField === 'sscc') {
          validatedValue = validateSerialNumbers(newValue, 'SSCC Serial Numbers');
          setSsccSerials(validatedValue);
        } else if (scannerModal.targetField === 'case') {
          validatedValue = validateSerialNumbers(newValue, 'Case Serial Numbers');
          setCaseSerials(validatedValue);
        } else if (scannerModal.targetField === 'innerCase') {
          validatedValue = validateSerialNumbers(newValue, 'Inner Case Serial Numbers');
          setInnerCaseSerials(validatedValue);
        } else {
          validatedValue = validateSerialNumbers(newValue, 'Item Serial Numbers');
          setItemSerials(validatedValue);
        }
        
        // Show detailed success message
        let successMessage = `Scanned serial number: ${parsedData.serialNumber}`;
        if (parsedData.gtin) {
          successMessage += `\nGTIN: ${parsedData.gtin}`;
        }
        if (parsedData.batchLot) {
          successMessage += `\nBatch/Lot: ${parsedData.batchLot}`;
        }
        if (parsedData.expirationDate) {
          successMessage += `\nExpiration: ${parsedData.expirationDate}`;
        }
        
        setSuccess(successMessage);
        
        // Close scanner
        closeScanner();
      } else {
        setError('Could not extract serial number from barcode');
      }
      
    } catch (error) {
      console.error('Error processing barcode:', error);
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

  // Scroll to top when step changes
  useEffect(() => {
    if (currentStep > 1) {
      scrollToTop();
    }
  }, [currentStep]);

  const calculateTotals = () => {
    // If no cases, items go directly in SSCC
    if (configuration.casesPerSscc === 0) {
      const totalItems = configuration.itemsPerCase * configuration.numberOfSscc;
      return { totalCases: 0, totalInnerCases: 0, totalItems };
    }
    
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

  const renderProgressBar = () => (
    <div className="progress-bar">
      <div 
        className={`progress-step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'clickable' : ''}`}
        onClick={() => handleStepClick(1)}
      >
        1
      </div>
      <div 
        className={`progress-step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'clickable' : ''}`}
        onClick={() => handleStepClick(2)}
      >
        2
      </div>
      <div 
        className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}
      >
        3
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="step-container">
      {renderProgressBar()}
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit}>
        
        <div className="epcclass-section">
          <h3>Product Information (EPCClass)</h3>
          <div className="form-grid">
            <div className="form-group fda-search-group">
              <label htmlFor="productNdc">Search FDA by Product NDC:</label>
              <div className="fda-search-container">
                <input
                  type="text"
                  id="productNdc"
                  value={configuration.productNdc}
                  onChange={(e) => setConfiguration({...configuration, productNdc: e.target.value})}
                  placeholder="e.g., 45802-466"
                  required
                />
                <button 
                  type="button" 
                  className="fda-search-button"
                  onClick={handleFdaSearch}
                  disabled={fdaModal.isLoading}
                >
                  {fdaModal.isLoading ? 'Searching...' : 'Search FDA Database'}
                </button>
              </div>
              <small className="form-hint">Enter 8-digit Product NDC to search FDA database for available package kinds</small>
            </div>
          </div>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="packageNdc">Package NDC (11-digit):</label>
              <input
                type="text"
                id="packageNdc"
                value={formatPackageNdc(configuration.packageNdc)}
                onChange={handlePackageNdcChange}
                placeholder="e.g., 45802-0466-53"
                maxLength="13"
                required
              />
              <small className="form-hint">11-digit NDC with hyphens for readability</small>
            </div>
            <div className="form-group">
              <label htmlFor="regulatedProductName">Regulated Product Name:</label>
              <input
                type="text"
                id="regulatedProductName"
                value={configuration.regulatedProductName}
                onChange={(e) => setConfiguration({...configuration, regulatedProductName: e.target.value})}
                placeholder="e.g., RX ECONAZOLE NITRATE 1% CRM 85G"
                required
              />
              <small className="form-hint">Official product name</small>
            </div>
          </div>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="manufacturerName">Manufacturer Name:</label>
              <input
                type="text"
                id="manufacturerName"
                value={configuration.manufacturerName}
                onChange={(e) => setConfiguration({...configuration, manufacturerName: e.target.value})}
                placeholder="e.g., Padagis LLC"
                required
              />
              <small className="form-hint">Manufacturer or labeler name</small>
            </div>
            <div className="form-group">
              <label htmlFor="dosageFormType">Dosage Form Type:</label>
              <input
                type="text"
                id="dosageFormType"
                value={configuration.dosageFormType}
                onChange={(e) => setConfiguration({...configuration, dosageFormType: e.target.value})}
                placeholder="e.g., CREAM"
                required
              />
              <small className="form-hint">Dosage form (e.g., TABLET, CREAM, INJECTION)</small>
            </div>
            <div className="form-group">
              <label htmlFor="strengthDescription">Strength Description:</label>
              <input
                type="text"
                id="strengthDescription"
                value={configuration.strengthDescription}
                onChange={(e) => setConfiguration({...configuration, strengthDescription: e.target.value})}
                placeholder="e.g., 10 mg/g"
                required
              />
              <small className="form-hint">Active ingredient strength</small>
            </div>
            <div className="form-group">
              <label htmlFor="netContentDescription">Net Content Description:</label>
              <input
                type="text"
                id="netContentDescription"
                value={configuration.netContentDescription}
                onChange={(e) => setConfiguration({...configuration, netContentDescription: e.target.value})}
                placeholder="e.g., 85GM     Wgt"
                required
              />
              <small className="form-hint">Package size and weight</small>
            </div>
            <div className="form-group">
              <label htmlFor="companyPrefix">Company Prefix:</label>
              <input
                type="text"
                id="companyPrefix"
                value={configuration.companyPrefix}
                onChange={(e) => setConfiguration({...configuration, companyPrefix: e.target.value})}
                placeholder="e.g., 0345802"
                required
              />
              <small className="form-hint">Your GS1 Company Prefix (auto-populated from NDC)</small>
            </div>
            <div className="form-group">
              <label htmlFor="productCode">Product Code:</label>
              <input
                type="text"
                id="productCode"
                value={configuration.productCode}
                onChange={(e) => setConfiguration({...configuration, productCode: e.target.value})}
                placeholder="e.g., 46653"
                required
              />
              <small className="form-hint">Product code from selected Package NDC</small>
            </div>
            <div className="form-group">
              <label htmlFor="lotNumber">Lot Number:</label>
              <input
                type="text"
                id="lotNumber"
                value={configuration.lotNumber}
                onChange={(e) => setConfiguration({...configuration, lotNumber: e.target.value})}
                placeholder="e.g., 4JT0482"
                required
              />
              <small className="form-hint">Lot number applied to Case, Inner Case, and Item levels</small>
            </div>
            <div className="form-group">
              <label htmlFor="expirationDate">Expiration Date:</label>
              <input
                type="date"
                id="expirationDate"
                value={configuration.expirationDate}
                onChange={(e) => setConfiguration({...configuration, expirationDate: e.target.value})}
                required
              />
              <small className="form-hint">Expiration date applied to Case, Inner Case, and Item levels</small>
            </div>
          </div>
        </div>

        <div className="inner-case-section">
          <h3>Packaging Configuration</h3>
          <div className="form-grid">
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
            <div className="form-group">
              <label htmlFor="casesPerSscc">Cases per SSCC:</label>
              <input
                type="number"
                id="casesPerSscc"
                min="0"
                max="50"
                value={configuration.casesPerSscc}
                onChange={(e) => setConfiguration({...configuration, casesPerSscc: parseInt(e.target.value)})}
                required
              />
              <small className="form-hint">Enter 0 for direct SSCC → Items aggregation</small>
            </div>
          </div>
          
          <div className="packaging-option">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={configuration.useInnerCases}
                onChange={(e) => setConfiguration({...configuration, useInnerCases: e.target.checked})}
                disabled={configuration.casesPerSscc === 0}
              />
              <span className="checkbox-text">
                <strong>Enable Inner Cases</strong>
                <small>{configuration.casesPerSscc === 0 ? 'Not available when Cases per SSCC = 0' : 'Add an intermediate packaging level between cases and items'}</small>
              </span>
            </label>
          </div>
          
          {configuration.casesPerSscc === 0 ? (
            <div className="packaging-config">
              <div className="config-explanation">
                <p><strong>2-Level Hierarchy:</strong> SSCC → Items</p>
              </div>
              <div className="form-group">
                <label htmlFor="itemsPerCase">Items per SSCC:</label>
                <input
                  type="number"
                  id="itemsPerCase"
                  min="1"
                  max="1000"
                  value={configuration.itemsPerCase}
                  onChange={(e) => setConfiguration({...configuration, itemsPerCase: parseInt(e.target.value)})}
                  required
                />
              </div>
            </div>
          ) : configuration.useInnerCases ? (
            <div className="packaging-config">
              <div className="config-explanation">
                <p><strong>4-Level Hierarchy:</strong> SSCC → Cases → Inner Cases → Items</p>
              </div>
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
            </div>
          ) : (
            <div className="packaging-config">
              <div className="config-explanation">
                <p><strong>3-Level Hierarchy:</strong> SSCC → Cases → Items</p>
              </div>
              <div className="form-group">
                <label htmlFor="itemsPerCase">Items per Case:</label>
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
            </div>
          )}
          
          <div className="gs1-indicators">
            <h4>GS1 Indicator Digits</h4>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="ssccExtensionDigit">SSCC Extension Digit:</label>
                <input
                  type="text"
                  id="ssccExtensionDigit"
                  maxLength="1"
                  value={configuration.ssccExtensionDigit}
                  onChange={(e) => setConfiguration({...configuration, ssccExtensionDigit: e.target.value})}
                  placeholder="0"
                  required
                />
                <small className="form-hint">Single digit (0-9) for SSCC extension</small>
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
        </div>
        
        <div className="hierarchy-section">
          <h3>Packaging Hierarchy</h3>
          <div className="hierarchy-visual">
            <div className="hierarchy-level">
              <strong>SSCCs:</strong> {configuration.numberOfSscc}
            </div>
            {configuration.casesPerSscc === 0 ? (
              <>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Items per SSCC:</strong> {configuration.itemsPerCase}
                </div>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Total Items:</strong> {calculateTotals().totalItems}
                </div>
              </>
            ) : (
              <>
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
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Items per Inner Case:</strong> {configuration.itemsPerInnerCase}
                    </div>
                  </>
                )}
                {!configuration.useInnerCases && (
                  <>
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Items per Case:</strong> {configuration.itemsPerCase}
                    </div>
                  </>
                )}
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Total Items:</strong> {calculateTotals().totalItems}
                </div>
              </>
            )}
          </div>
          
          <div className="gs1-examples">
            <h4>GS1 Identifier Examples</h4>
            <p><strong>SSCC:</strong> urn:epc:id:sscc:{configuration.companyPrefix}.{configuration.ssccExtensionDigit}[sscc_serial]</p>
            <p><strong>Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.caseIndicatorDigit}{configuration.productCode}.[case_serial]</p>
            {configuration.useInnerCases && (
              <p><strong>Inner Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.innerCaseIndicatorDigit}{configuration.productCode}.[inner_case_serial]</p>
            )}
            <p><strong>Item SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.itemIndicatorDigit}{configuration.productCode}.[item_serial]</p>
          </div>
        </div>
        
        <div className="config-actions">
          <button type="submit" disabled={isLoading} className="btn-primary">
            {isLoading ? 'Saving...' : 'Save Configuration'}
            <FiChevronRight className="ml-2" />
          </button>
        </div>
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
        {renderProgressBar()}
        <h2 className="step-title">Step 2: Serial Numbers</h2>
        <form onSubmit={handleSerialNumbersSubmit} className="serial-form">
          
          <div className="serial-section">
            <h3>SSCC Serial Numbers 
              <span className={`counter ${ssccCount === configuration.numberOfSscc ? 'counter-complete' : ''}`}>
                ({ssccCount}/{configuration.numberOfSscc})
              </span>
            </h3>
            <div className="textarea-group">
              <textarea
                value={ssccSerials}
                onChange={handleSsccSerialsChange}
                placeholder="Enter SSCC serial numbers, one per line"
                rows="5"
                required
              />
              <small className="form-hint">Enter {configuration.numberOfSscc} SSCC serial numbers, one per line</small>
            </div>
          </div>

          {totals.totalCases > 0 && (
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
                    onChange={handleCaseSerialsChange}
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
                    <FiCamera size={20} />
                  </button>
                </div>
                <small className="form-hint">Enter {totals.totalCases} case serial numbers, one per line</small>
              </div>
            </div>
          )}

          {configuration.useInnerCases && totals.totalInnerCases > 0 && (
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
                    onChange={handleInnerCaseSerialsChange}
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
                    <FiCamera size={20} />
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
                  onChange={handleItemSerialsChange}
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
                  <FiCamera size={20} />
                </button>
              </div>
              <small className="form-hint">Enter {totals.totalItems} item serial numbers, one per line</small>
            </div>
          </div>

          <div className="button-group">
            <button 
              type="button" 
              onClick={() => {
                setCurrentStep(1);
                scrollToTop();
              }} 
              className="btn-secondary"
            >
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
        {renderProgressBar()}
        <h2 className="step-title">Step 3: Generate EPCIS File</h2>
        
        <div className="summary-section">
          <h3>Configuration Summary</h3>
          
          {/* Package Hierarchy */}
          <div className="summary-card">
            <h4>Package Hierarchy</h4>
            <div className="hierarchy-summary">
              <div className="hierarchy-item">
                <span className="hierarchy-label">SSCCs</span>
                <span className="hierarchy-value">{configuration.numberOfSscc}</span>
              </div>
              
              {configuration.casesPerSscc > 0 && (
                <>
                  <div className="hierarchy-arrow">→</div>
                  <div className="hierarchy-item">
                    <span className="hierarchy-label">Cases</span>
                    <span className="hierarchy-value">{totals.totalCases}</span>
                  </div>
                </>
              )}
              
              {configuration.useInnerCases && (
                <>
                  <div className="hierarchy-arrow">→</div>
                  <div className="hierarchy-item">
                    <span className="hierarchy-label">Inner Cases</span>
                    <span className="hierarchy-value">{totals.totalInnerCases}</span>
                  </div>
                </>
              )}
              
              <div className="hierarchy-arrow">→</div>
              <div className="hierarchy-item">
                <span className="hierarchy-label">Items</span>
                <span className="hierarchy-value">{totals.totalItems}</span>
              </div>
            </div>
          </div>

          {/* GS1 Configuration */}
          <div className="summary-card">
            <h4>GS1 Configuration</h4>
            <div className="config-details">
              <div className="config-row">
                <span className="config-label">Company Prefix</span>
                <span className="config-value">{configuration.companyPrefix}</span>
              </div>
              <div className="config-row">
                <span className="config-label">Product Code</span>
                <span className="config-value">{configuration.productCode}</span>
              </div>
              <div className="config-row">
                <span className="config-label">Lot Number</span>
                <span className="config-value">{configuration.lotNumber}</span>
              </div>
              <div className="config-row">
                <span className="config-label">Expiration Date</span>
                <span className="config-value">{configuration.expirationDate}</span>
              </div>
            </div>
          </div>

          {/* EPCIS Details */}
          <div className="summary-card epcis-card">
            <h4>EPCIS File Details</h4>
            <div className="epcis-details">
              <div className="epcis-row">
                <span className="epcis-label">Format</span>
                <span className="epcis-value">EPCIS 1.2 Standard</span>
              </div>
              <div className="epcis-row">
                <span className="epcis-label">Event Types</span>
                <span className="epcis-value">Commissioning + Aggregation</span>
              </div>
              <div className="epcis-row">
                <span className="epcis-label">Business Step</span>
                <span className="epcis-value">Commissioning + Packing</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="button-group">
          <button 
            type="button" 
            onClick={() => {
              setCurrentStep(2);
              scrollToTop();
            }} 
            className="btn-secondary"
          >
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
          <div className="header-content">
            <img className="header-logo" src="https://cdn.prod.website-files.com/6154ee5ad4b73423326331fd/66a2bd8c5b618c82f5e30699_rxerp-logo-hero-light.svg"></img>
            <div className="header-text">
              <h1>RxERP Aggregator</h1>
              <p>Generate GS1 compliant EPCIS files for pharmaceutical serialization</p>
            </div>
          </div>
        </header>

        <main className="main-content">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </main>

        {/* Toast Notifications */}
        <div className="toast-container">
          {error && (
            <div className={`toast toast-error ${isToastExiting ? 'toast-exit' : ''}`}>
              <span>{error}</span>
              <button className="toast-close" onClick={() => dismissAlert('error')}>×</button>
              <div className="toast-progress"></div>
            </div>
          )}
          {success && (
            <div className={`toast toast-success ${isToastExiting ? 'toast-exit' : ''}`}>
              <span>{success}</span>
              <button className="toast-close" onClick={() => dismissAlert('success')}>×</button>
              <div className="toast-progress"></div>
            </div>
          )}
        </div>

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

        {/* FDA API Search Modal */}
        {fdaModal.isOpen && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>Select Product Packaging</h3>
                <button className="close-button" onClick={closeFdaModal}>×</button>
              </div>
              <div className="modal-body">
                {fdaModal.searchResults.length > 0 ? (
                  <div className="fda-results">
                    <p className="modal-instruction">Select the packaging option for this product:</p>
                    {fdaModal.searchResults.map((productOption, index) => (
                      <div key={index} className="fda-result-item" onClick={() => selectFdaProduct(productOption)}>
                        <div className="fda-product-header">
                          <h4>{productOption.brand_name || productOption.generic_name}</h4>
                          <div className="fda-ndc-badge">
                            <span className="ndc-label">Product NDC:</span>
                            <span className="ndc-value">{productOption.product_ndc}</span>
                          </div>
                        </div>
                        
                        <div className="fda-product-details">
                          <p><strong>Manufacturer:</strong> {productOption.labeler_name}</p>
                          <p><strong>Dosage Form:</strong> {productOption.dosage_form}</p>
                          {productOption.active_ingredients && (
                            <p><strong>Active Ingredients:</strong> {productOption.active_ingredients.map(ing => `${ing.name} ${ing.strength}`).join(', ')}</p>
                          )}
                        </div>
                        
                        <div className="fda-packaging-info">
                          <div className="packaging-header">
                            <strong>Package NDC:</strong> {productOption.packageNdc}
                          </div>
                          <div className="packaging-description">
                            <strong>Package Description:</strong> {productOption.packageDescription}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No packaging options found</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;