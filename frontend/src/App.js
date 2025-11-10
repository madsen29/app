import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { FiCamera, FiChevronRight, FiPackage, FiBox, FiFolder, FiFile, FiX, FiArrowLeft } from 'react-icons/fi';
import { useAuth } from './AuthContext';
import AuthWrapper from './AuthWrapper';

// ScandIt Integration - Working Implementation
import SimpleScandItScanner from './SimpleScandItScanner';
import ProjectDashboard from './ProjectDashboard';
import LocationSelector from './LocationSelector';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const { user, logout } = useAuth();
  
  // Project management state
  const [currentProject, setCurrentProject] = useState(null);
  const [showDashboard, setShowDashboard] = useState(true);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isPackagingConfigLocked, setIsPackagingConfigLocked] = useState(false);
  const [originalPackagingConfig, setOriginalPackagingConfig] = useState(null);
  
  // Existing state
  const [currentStep, setCurrentStep] = useState(1);
  
  // Multi-product configuration state
  const [products, setProducts] = useState([
    {
      id: 'product-1',
      // Product Information (EPCClass)
      manufacturerName: '',
      regulatedProductName: '',
      packageNdc: '',
      productNdc: '',
      dosageFormType: '',
      strengthDescription: '',
      netContentDescription: '',
      companyPrefix: '',
      productCode: '',
      lotNumber: '',
      expirationDate: '',
      
      // Packaging Configuration (per product)
      itemsPerCase: '',
      casesPerSscc: '',
      numberOfSscc: 1,
      useInnerCases: false,
      innerCasesPerCase: '',
      itemsPerInnerCase: '',
      ssccExtensionDigit: '0',
      caseIndicatorDigit: '0',
      innerCaseIndicatorDigit: '0',
      itemIndicatorDigit: '0'
    }
  ]);
  
  // Active product index for UI
  const [activeProductIndex, setActiveProductIndex] = useState(0);
  
  // Legacy configuration state (for backward compatibility)
  const [configuration, setConfiguration] = useState({
    itemsPerCase: '',
    casesPerSscc: '',
    numberOfSscc: '',
    useInnerCases: false,
    innerCasesPerCase: '',
    itemsPerInnerCase: '',
    companyPrefix: '',
    productCode: '',
    lotNumber: '',
    expirationDate: '',
    ssccExtensionDigit: '0',
    caseIndicatorDigit: '0',
    innerCaseIndicatorDigit: '0',
    itemIndicatorDigit: '0',
    // Business Document Information
    senderCompanyPrefix: '',
    senderGln: '',
    senderSgln: '',
    senderName: '',
    senderStreetAddress: '',
    senderCity: '',
    senderState: '',
    senderPostalCode: '',
    senderCountryCode: '',
    senderDespatchAdviceNumber: '',
    receiverCompanyPrefix: '',
    receiverGln: '',
    receiverSgln: '',
    receiverName: '',
    receiverStreetAddress: '',
    receiverCity: '',
    receiverState: '',
    receiverPostalCode: '',
    receiverCountryCode: '',
    receiverPoNumber: '',
    shipperCompanyPrefix: '',
    shipperGln: '',
    shipperSgln: '',
    shipperName: '',
    shipperStreetAddress: '',
    shipperCity: '',
    shipperState: '',
    shipperPostalCode: '',
    shipperCountryCode: '',
    shipperSameAsSender: false,
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
  // Scanner states and refs
  const [scannerModal, setScannerModal] = useState({ isOpen: false, targetField: '', currentValue: '' });
  const [isScanning, setIsScanning] = useState(false);
  const [scannedItems, setScannedItems] = useState([]);
  const [shouldContinueScanning, setShouldContinueScanning] = useState(false);
  
  // ScandIt scanner refs
  const scandItScannerRef = useRef(null);
  const scannerContainerRef = useRef(null);

  // ScandIt License Key (your working license key)
  const SCANDIT_LICENSE_KEY = "Avq2K9OBRx04MGjA0PBXZNg0GJdPLM/Tfykv+wm9WZBVMtoG93WJHfBxpgo7WGNWmHhHRFtEYJpecdnrBgWsLAkdP5ZlYq63v1+63fVPf0KUV3PNwWq1+VlGD4D4XeZCZVBLaapqykHhca2fSWOu1WElRQo0XGK91WeblTlU53qTM7MK8hbiYPACkBWcGhbbFuBvDnuTCGVyLUjoVKZOVi77ChaJYMUb53gt+YWWf5ZyO8WYr+zkgXcUkN7VFtqzuvSZhKQAz9R9FVTqSg5yfS3LmMNk0EtcpOurlgxKtIkZA2zB0hk+AC73W+clFYW0hUivDlIa+3FmYA2YUaUurvXm8FdCNUJoGDQC3le7JX0T2Fxem9G/yIuVV1qQwDHVgGXon0DbBde2jCy28YlqypdViFKseHq4yVWCwxno8/rcGVzj6M3By/ZCy72aQifK1qi/4/FYBlNsyW8Q2XZKtn9EZns8B6vIMcn25WpUvyiAL9PbkiaX2TM+/9a1peyw3zytVg26fyuxcbKNdkDvlFZA/TIuEiQqltkohZuxmGfwGojeT6U2eGWdoGiX8Z2CVkm00JNU302QKkSxvf0F/igdZhZW9HDJQfXSFX8zStGz/jf09CAND+EWlJj7qEO3Pkmi/n3o+ZDnjdiT9NYH3InzoeoLLBsxkZi1FObPf+FtSgNmytMcJWERiKUegF1nQJLyKU3pWoo6OqNWXiV7BjQsMukyW8G+Ti0+rPtmKnR/cA2Vjx4rQxRx1ukltI2tMMHteVzVYXa9BkuGu0b4eWQAH4EB4GarCgkK30aOx6nMB+yDioH+aeZxBBK+F7tu7N3CibuyddHe6ncCSpSBjG/0O3n2mylP6zn80L/z";

  const [requiredItemCount, setRequiredItemCount] = useState(1);
  const [fdaModal, setFdaModal] = useState({ isOpen: false, searchResults: [], isLoading: false });
  const [editModal, setEditModal] = useState({ isOpen: false, path: '', currentValue: '', label: '', contextPath: '' });
  
  // User Settings modal state
  const [showUserSettings, setShowUserSettings] = useState(false);
  
  // Location Selector modal state
  const [locationSelectorModal, setLocationSelectorModal] = useState({
    isOpen: false,
    targetSection: null // 'sender', 'receiver', or 'shipper'
  });

  // Location selector functions
  const openLocationSelector = (targetSection) => {
    setLocationSelectorModal({
      isOpen: true,
      targetSection: targetSection
    });
  };

  const closeLocationSelector = () => {
    setLocationSelectorModal({
      isOpen: false,
      targetSection: null
    });
  };

  const handleLocationSelected = (locationData) => {
    setConfiguration(prevConfig => ({
      ...prevConfig,
      ...locationData
    }));
    setHasUnsavedChanges(true);
  };
  
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const [autoSaveTimer, setAutoSaveTimer] = useState(null);

  // Auto-dismiss toast after 4 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        dismissToast();
      }, 4000);
      
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // Auto-update shipper fields when sender changes and checkbox is checked
  useEffect(() => {
    if (configuration.shipperSameAsSender) {
      setConfiguration(prev => ({
        ...prev,
        shipperCompanyPrefix: prev.senderCompanyPrefix,
        shipperGln: prev.senderGln,
        shipperSgln: prev.senderSgln,
        shipperName: prev.senderName,
        shipperStreetAddress: prev.senderStreetAddress,
        shipperCity: prev.senderCity,
        shipperState: prev.senderState,
        shipperPostalCode: prev.senderPostalCode,
        shipperCountryCode: prev.senderCountryCode
      }));
    }
  }, [
    configuration.senderCompanyPrefix, 
    configuration.senderGln, 
    configuration.senderSgln,
    configuration.senderName,
    configuration.senderStreetAddress,
    configuration.senderCity,
    configuration.senderState,
    configuration.senderPostalCode,
    configuration.senderCountryCode,
    configuration.senderDespatchAdviceNumber,
    configuration.shipperSameAsSender
  ]);

  // Track unsaved changes
  useEffect(() => {
    if (currentProject) {
      setHasUnsavedChanges(true);
    }
  }, [configuration, hierarchicalSerials]);

  // Handle browser refresh/close warning
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  // Auto-save configuration changes
  useEffect(() => {
    if (currentProject && hasUnsavedChanges) {
      debouncedAutoSave();
    }
  }, [configuration]);

  // Auto-save serial numbers changes
  useEffect(() => {
    if (currentProject && hasUnsavedChanges && hierarchicalSerials.length > 0) {
      debouncedAutoSave();
    }
  }, [hierarchicalSerials]);

  // Cleanup auto-save timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }
    };
  }, [autoSaveTimer]);

  const dismissToast = () => {
    setIsToastExiting(true);
    setTimeout(() => {
      setError('');
      setSuccess('');
      setIsToastExiting(false);
    }, 300); // Match animation duration
  };

  // Auto-save functionality for serial numbers
  const autoSaveSerialNumbers = async (updatedSerials) => {
    if (!currentProject) return;
    
    try {
      await axios.put(`${API}/projects/${currentProject.id}`, {
        serial_numbers: updatedSerials,
        updated_at: new Date().toISOString()
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setHasUnsavedChanges(false);
      console.log('Serial numbers auto-saved');
    } catch (err) {
      console.error('Auto-save failed:', err);
      // Don't show error to user for auto-save failures
    }
  };

  // Helper function to find the current position in serial collection
  const findCurrentSerialPosition = (hierarchicalData, config) => {
    // We need to check against the expected configuration structure
    const expectedSSCCs = config.numberOfSscc || 1;
    const expectedCasesPerSSCC = config.casesPerSscc || 0;
    const expectedInnerCasesPerCase = config.innerCasesPerCase || 0;
    const expectedItemsPerCase = config.itemsPerCase || 10;
    const expectedItemsPerInnerCase = config.itemsPerInnerCase || 5;
    const useInnerCases = config.useInnerCases || false;
    
    for (let ssccIndex = 0; ssccIndex < expectedSSCCs; ssccIndex++) {
      const ssccData = hierarchicalData[ssccIndex];
      
      // Check if this SSCC doesn't exist or has no serial
      if (!ssccData || !ssccData.ssccSerial) {
        return {
          ssccIndex,
          caseIndex: 0,
          innerCaseIndex: 0,
          itemIndex: 0,
          currentLevel: 'sscc',
          isComplete: false
        };
      }
      
      // Check cases
      if (expectedCasesPerSSCC > 0) {
        for (let caseIndex = 0; caseIndex < expectedCasesPerSSCC; caseIndex++) {
          const caseData = ssccData.cases && ssccData.cases[caseIndex];
          
          // Check if case doesn't exist or has no serial
          if (!caseData || !caseData.caseSerial) {
            return {
              ssccIndex,
              caseIndex,
              innerCaseIndex: 0,
              itemIndex: 0,
              currentLevel: 'case',
              isComplete: false
            };
          }
          
          // Check inner cases
          if (useInnerCases) {
            for (let innerCaseIndex = 0; innerCaseIndex < expectedInnerCasesPerCase; innerCaseIndex++) {
              const innerCaseData = caseData.innerCases && caseData.innerCases[innerCaseIndex];
              
              // Check if inner case doesn't exist or has no serial
              if (!innerCaseData || !innerCaseData.innerCaseSerial) {
                return {
                  ssccIndex,
                  caseIndex,
                  innerCaseIndex,
                  itemIndex: 0,
                  currentLevel: 'innerCase',
                  isComplete: false
                };
              }
              
              // Check items in inner case
              for (let itemIndex = 0; itemIndex < expectedItemsPerInnerCase; itemIndex++) {
                const itemData = innerCaseData.items && innerCaseData.items[itemIndex];
                if (!itemData || !itemData.itemSerial) {
                  return {
                    ssccIndex,
                    caseIndex,
                    innerCaseIndex,
                    itemIndex,
                    currentLevel: 'item',
                    isComplete: false
                  };
                }
              }
            }
          } else {
            // Check items in case (no inner cases)
            for (let itemIndex = 0; itemIndex < expectedItemsPerCase; itemIndex++) {
              const itemData = caseData.items && caseData.items[itemIndex];
              if (!itemData || !itemData.itemSerial) {
                return {
                  ssccIndex,
                  caseIndex,
                  innerCaseIndex: 0,
                  itemIndex,
                  currentLevel: 'item',
                  isComplete: false
                };
              }
            }
          }
        }
      } else {
        // Direct SSCC → Items
        for (let itemIndex = 0; itemIndex < expectedItemsPerCase; itemIndex++) {
          const itemData = ssccData.items && ssccData.items[itemIndex];
          if (!itemData || !itemData.itemSerial) {
            return {
              ssccIndex,
              caseIndex: 0,
              innerCaseIndex: 0,
              itemIndex,
              currentLevel: 'item',
              isComplete: false
            };
          }
        }
      }
    }
    
    // All serials are complete
    return {
      ssccIndex: expectedSSCCs - 1,
      caseIndex: 0,
      innerCaseIndex: 0,
      itemIndex: 0,
      currentLevel: 'item',
      isComplete: true
    };
  };

  // Project management functions
  const handleSelectProject = (project) => {
    // CRITICAL: Clear any existing serial state to prevent cross-project contamination
    setHierarchicalSerials([]);
    
    setCurrentProject(project);
    setShowDashboard(false);
    setHasUnsavedChanges(false); // Reset unsaved changes flag
    
    // Reset packaging configuration lock state for new project selection
    setIsPackagingConfigLocked(false);
    setOriginalPackagingConfig(null);
    
    // Helper function to get configuration value (handles both camelCase and snake_case)
    const getConfigValue = (config, camelKey, snakeKey, defaultValue) => {
      // Properly handle falsy values by checking for undefined/null instead of using ||
      if (config[camelKey] !== undefined && config[camelKey] !== null) {
        return config[camelKey];
      } else if (config[snakeKey] !== undefined && config[snakeKey] !== null) {
        return config[snakeKey];
      } else {
        return defaultValue;
      }
    };
    
    // Helper function to get numeric configuration value
    const getNumericConfigValue = (config, camelKey, snakeKey, defaultValue) => {
      // Properly handle 0 values by checking for undefined/null instead of using ||
      let value;
      if (config[camelKey] !== undefined && config[camelKey] !== null) {
        value = config[camelKey];
      } else if (config[snakeKey] !== undefined && config[snakeKey] !== null) {
        value = config[snakeKey];
      } else {
        value = defaultValue;
      }
      
      const parsed = parseInt(value);
      // Return parsed value if it's a valid number (including 0), otherwise return defaultValue
      return !isNaN(parsed) ? parsed : defaultValue;
    };
    
    // Load project configuration - handle both multi-product and legacy formats
    if (project.configuration) {
      const config = project.configuration;
      console.log('Loading project configuration:', config);
      
      // Check if this is a multi-product configuration
      if (config.products && Array.isArray(config.products)) {
        // Multi-product format
        console.log('Loading multi-product configuration');
        setProducts(config.products);
        setActiveProductIndex(0);
        
        // Sync legacy configuration with first product for backward compatibility
        if (config.products.length > 0) {
          setConfiguration({...config.products[0]});
        }
      } else {
        // Legacy single-product format - convert to multi-product
        console.log('Converting legacy single-product to multi-product format');
        const legacyProduct = {
          id: 'legacy-product',
          itemsPerCase: getNumericConfigValue(config, 'itemsPerCase', 'items_per_case', ''),
          casesPerSscc: getNumericConfigValue(config, 'casesPerSscc', 'cases_per_sscc', ''),
          numberOfSscc: getNumericConfigValue(config, 'numberOfSscc', 'number_of_sscc', ''),
          useInnerCases: getConfigValue(config, 'useInnerCases', 'use_inner_cases', false),
          innerCasesPerCase: getNumericConfigValue(config, 'innerCasesPerCase', 'inner_cases_per_case', ''),
          itemsPerInnerCase: getNumericConfigValue(config, 'itemsPerInnerCase', 'items_per_inner_case', ''),
          companyPrefix: getConfigValue(config, 'companyPrefix', 'company_prefix', ''),
          productCode: getConfigValue(config, 'productCode', 'product_code', ''),
          lotNumber: getConfigValue(config, 'lotNumber', 'lot_number', ''),
          expirationDate: getConfigValue(config, 'expirationDate', 'expiration_date', ''),
          ssccExtensionDigit: getConfigValue(config, 'ssccExtensionDigit', 'sscc_extension_digit', '0'),
          caseIndicatorDigit: getConfigValue(config, 'caseIndicatorDigit', 'case_indicator_digit', '0'),
          innerCaseIndicatorDigit: getConfigValue(config, 'innerCaseIndicatorDigit', 'inner_case_indicator_digit', '0'),
          itemIndicatorDigit: getConfigValue(config, 'itemIndicatorDigit', 'item_indicator_digit', '0'),
          manufacturerName: getConfigValue(config, 'manufacturerName', 'manufacturer_name', ''),
          regulatedProductName: getConfigValue(config, 'regulatedProductName', 'regulated_product_name', ''),
          packageNdc: getConfigValue(config, 'packageNdc', 'package_ndc', ''),
          productNdc: getConfigValue(config, 'productNdc', 'product_ndc', ''),
          dosageFormType: getConfigValue(config, 'dosageFormType', 'dosage_form_type', ''),
          strengthDescription: getConfigValue(config, 'strengthDescription', 'strength_description', ''),
          netContentDescription: getConfigValue(config, 'netContentDescription', 'net_content_description', '')
        };
        
        setProducts([legacyProduct]);
        setActiveProductIndex(0);
        setConfiguration({
          ...legacyProduct,
          // Business Document Information
          senderCompanyPrefix: getConfigValue(config, 'senderCompanyPrefix', 'sender_company_prefix', ''),
          senderGln: getConfigValue(config, 'senderGln', 'sender_gln', ''),
          senderSgln: getConfigValue(config, 'senderSgln', 'sender_sgln', ''),
          senderName: getConfigValue(config, 'senderName', 'sender_name', ''),
          senderStreetAddress: getConfigValue(config, 'senderStreetAddress', 'sender_street_address', ''),
          senderCity: getConfigValue(config, 'senderCity', 'sender_city', ''),
          senderState: getConfigValue(config, 'senderState', 'sender_state', ''),
          senderPostalCode: getConfigValue(config, 'senderPostalCode', 'sender_postal_code', ''),
          senderCountryCode: getConfigValue(config, 'senderCountryCode', 'sender_country_code', ''),
          senderDespatchAdviceNumber: getConfigValue(config, 'senderDespatchAdviceNumber', 'sender_despatch_advice_number', ''),
          receiverCompanyPrefix: getConfigValue(config, 'receiverCompanyPrefix', 'receiver_company_prefix', ''),
          receiverGln: getConfigValue(config, 'receiverGln', 'receiver_gln', ''),
          receiverSgln: getConfigValue(config, 'receiverSgln', 'receiver_sgln', ''),
          receiverName: getConfigValue(config, 'receiverName', 'receiver_name', ''),
          receiverStreetAddress: getConfigValue(config, 'receiverStreetAddress', 'receiver_street_address', ''),
          receiverCity: getConfigValue(config, 'receiverCity', 'receiver_city', ''),
          receiverState: getConfigValue(config, 'receiverState', 'receiver_state', ''),
          receiverPostalCode: getConfigValue(config, 'receiverPostalCode', 'receiver_postal_code', ''),
          receiverCountryCode: getConfigValue(config, 'receiverCountryCode', 'receiver_country_code', ''),
          receiverPoNumber: getConfigValue(config, 'receiverPoNumber', 'receiver_po_number', ''),
          shipperCompanyPrefix: getConfigValue(config, 'shipperCompanyPrefix', 'shipper_company_prefix', ''),
          shipperGln: getConfigValue(config, 'shipperGln', 'shipper_gln', ''),
          shipperSgln: getConfigValue(config, 'shipperSgln', 'shipper_sgln', ''),
          shipperName: getConfigValue(config, 'shipperName', 'shipper_name', ''),
          shipperStreetAddress: getConfigValue(config, 'shipperStreetAddress', 'shipper_street_address', ''),
          shipperCity: getConfigValue(config, 'shipperCity', 'shipper_city', ''),
          shipperState: getConfigValue(config, 'shipperState', 'shipper_state', ''),
          shipperPostalCode: getConfigValue(config, 'shipperPostalCode', 'shipper_postal_code', ''),
          shipperCountryCode: getConfigValue(config, 'shipperCountryCode', 'shipper_country_code', ''),
          shipperSameAsSender: getConfigValue(config, 'shipperSameAsSender', 'shipper_same_as_sender', false)
        });
      }
    }
    
    // Set current step based on project state
    // For completed projects, always go to Step 3 for editing
    if (project.status === 'Completed') {
      setCurrentStep(3);
    } else {
      setCurrentStep(project.current_step || 1);
    }
    
    // Check if packaging configuration should be locked
    const hasSerialNumbers = project.serial_numbers && project.serial_numbers.length > 0;
    setIsPackagingConfigLocked(hasSerialNumbers);
    
    // Store original packaging configuration for comparison
    if (project.configuration) {
      const config = project.configuration;
      setOriginalPackagingConfig({
        itemsPerCase: getNumericConfigValue(config, 'itemsPerCase', 'items_per_case', ''),
        casesPerSscc: getNumericConfigValue(config, 'casesPerSscc', 'cases_per_sscc', ''),
        numberOfSscc: getNumericConfigValue(config, 'numberOfSscc', 'number_of_sscc', ''),
        useInnerCases: getConfigValue(config, 'useInnerCases', 'use_inner_cases', false),
        innerCasesPerCase: getNumericConfigValue(config, 'innerCasesPerCase', 'inner_cases_per_case', ''),
        itemsPerInnerCase: getNumericConfigValue(config, 'itemsPerInnerCase', 'items_per_inner_case', '')
      });
    }
    
    // Load existing serial numbers if available
    if (project.serial_numbers) {
      setHierarchicalSerials(project.serial_numbers);
      
      // For completed projects or projects on step 2, restore the serial collection step state
      if ((project.status === 'Completed' || project.current_step === 2) && project.configuration) {
        // Find the current position in the serial collection
        const currentPosition = findCurrentSerialPosition(project.serial_numbers, project.configuration);
        if (currentPosition.isComplete || project.status === 'Completed') {
          // For completed projects, always set serial collection as complete
          setSerialCollectionStep({
            ...currentPosition,
            isComplete: true
          });
        } else {
          setSerialCollectionStep({
            ...currentPosition,
            currentSerial: '',
            isComplete: false
          });
        }
      }
    } else if (project.configuration && project.current_step >= 2) {
      // Initialize hierarchical serials if we're on step 2 or beyond but don't have saved serial numbers
      initializeHierarchicalSerials(project.configuration);
    }
  };

  const handleBackToDashboard = async () => {
    // Auto-save before exiting if there are unsaved changes
    if (hasUnsavedChanges) {
      await autoSaveBeforeExit();
    }
    
    setShowDashboard(true);
    setCurrentProject(null);
    setCurrentStep(1);
    setHasUnsavedChanges(false);
    setIsPackagingConfigLocked(false);
    setOriginalPackagingConfig(null);
    
    // Clear any existing auto-save timer
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
      setAutoSaveTimer(null);
    }
    
    // Reset configuration to defaults
    setConfiguration({
      itemsPerCase: '',
      casesPerSscc: '',
      numberOfSscc: '',
      useInnerCases: false,
      innerCasesPerCase: '',
      itemsPerInnerCase: '',
      companyPrefix: '',
      productCode: '',
      lotNumber: '',
      expirationDate: '',
      ssccExtensionDigit: '0',
      caseIndicatorDigit: '0',
      innerCaseIndicatorDigit: '0',
      itemIndicatorDigit: '0',
      // Business Document Information
      senderCompanyPrefix: '',
      senderGln: '',
      senderSgln: '',
      senderName: '',
      senderStreetAddress: '',
      senderCity: '',
      senderState: '',
      senderPostalCode: '',
      senderCountryCode: '',
      senderDespatchAdviceNumber: '',
      receiverCompanyPrefix: '',
      receiverGln: '',
      receiverSgln: '',
      receiverName: '',
      receiverStreetAddress: '',
      receiverCity: '',
      receiverState: '',
      receiverPostalCode: '',
      receiverCountryCode: '',
      receiverPoNumber: '',
      shipperCompanyPrefix: '',
      shipperGln: '',
      shipperSgln: '',
      shipperName: '',
      shipperStreetAddress: '',
      shipperCity: '',
      shipperState: '',
      shipperPostalCode: '',
      shipperCountryCode: '',
      shipperSameAsSender: false,
      // EPCClass data
      productNdc: '',
      packageNdc: '',
      regulatedProductName: '',
      manufacturerName: '',
      dosageFormType: '',
      strengthDescription: '',
      netContentDescription: ''
    });
    
    // Reset serial collection step to initial state (but preserve hierarchicalSerials)
    // DO NOT clear hierarchicalSerials here as it causes data loss during complex navigation
    setSerialCollectionStep({
      ssccIndex: 0,
      caseIndex: 0,
      innerCaseIndex: 0,
      itemIndex: 0,
      currentLevel: 'sscc',
      currentSerial: '',
      isComplete: false
    });
  };

  const handleLogout = () => {
    logout();
    handleBackToDashboard();
  };

  // Save Progress functionality
  const handleSaveProgress = async (showToast = true) => {
    if (!currentProject) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      // Determine the actual step based on progress, not just the current UI step
      let actualStep = currentStep;
      
      // If user has serial numbers entered, they should be on step 2 minimum
      if (hierarchicalSerials && hierarchicalSerials.length > 0) {
        const hasAnySerials = hierarchicalSerials.some(sscc => 
          (sscc.ssccSerial && sscc.ssccSerial.trim()) ||
          (sscc.cases && sscc.cases.some(caseData => 
            (caseData.caseSerial && caseData.caseSerial.trim()) ||
            (caseData.items && caseData.items.some(item => item.itemSerial && item.itemSerial.trim())) ||
            (caseData.innerCases && caseData.innerCases.some(innerCase => 
              (innerCase.innerCaseSerial && innerCase.innerCaseSerial.trim()) ||
              (innerCase.items && innerCase.items.some(item => item.itemSerial && item.itemSerial.trim()))
            ))
          )) ||
          (sscc.items && sscc.items.some(item => item.itemSerial && item.itemSerial.trim()))
        );
        
        if (hasAnySerials && actualStep < 2) {
          actualStep = 2; // Keep them on step 2 if they have serial progress
        }
      }
      
      const updateData = {
        current_step: actualStep,
        updated_at: new Date().toISOString()
      };

      // Save configuration if we're on step 1 or beyond
      if (currentStep >= 1) {
        console.log('Saving multi-product configuration');
        updateData.configuration = {
          // Multi-product format
          products: products,
          
          // Legacy fields for backward compatibility
          itemsPerCase: configuration.itemsPerCase,
          casesPerSscc: configuration.casesPerSscc,
          numberOfSscc: configuration.numberOfSscc,
          useInnerCases: configuration.useInnerCases,
          innerCasesPerCase: configuration.innerCasesPerCase,
          itemsPerInnerCase: configuration.itemsPerInnerCase,
          companyPrefix: configuration.companyPrefix,
          productCode: configuration.productCode,
          lotNumber: configuration.lotNumber,
          expirationDate: configuration.expirationDate,
          ssccExtensionDigit: configuration.ssccExtensionDigit,
          caseIndicatorDigit: configuration.caseIndicatorDigit,
          innerCaseIndicatorDigit: configuration.innerCaseIndicatorDigit,
          itemIndicatorDigit: configuration.itemIndicatorDigit,
          // Business Document Information
          senderCompanyPrefix: configuration.senderCompanyPrefix,
          senderGln: configuration.senderGln,
          senderSgln: configuration.senderSgln,
          senderName: configuration.senderName,
          senderStreetAddress: configuration.senderStreetAddress,
          senderCity: configuration.senderCity,
          senderState: configuration.senderState,
          senderPostalCode: configuration.senderPostalCode,
          senderCountryCode: configuration.senderCountryCode,
          senderDespatchAdviceNumber: configuration.senderDespatchAdviceNumber,
          receiverCompanyPrefix: configuration.receiverCompanyPrefix,
          receiverGln: configuration.receiverGln,
          receiverSgln: configuration.receiverSgln,
          receiverName: configuration.receiverName,
          receiverStreetAddress: configuration.receiverStreetAddress,
          receiverCity: configuration.receiverCity,
          receiverState: configuration.receiverState,
          receiverPostalCode: configuration.receiverPostalCode,
          receiverCountryCode: configuration.receiverCountryCode,
          receiverPoNumber: configuration.receiverPoNumber,
          shipperCompanyPrefix: configuration.shipperCompanyPrefix,
          shipperGln: configuration.shipperGln,
          shipperSgln: configuration.shipperSgln,
          shipperName: configuration.shipperName,
          shipperStreetAddress: configuration.shipperStreetAddress,
          shipperCity: configuration.shipperCity,
          shipperState: configuration.shipperState,
          shipperPostalCode: configuration.shipperPostalCode,
          shipperCountryCode: configuration.shipperCountryCode,
          shipperSameAsSender: configuration.shipperSameAsSender,
          // EPCClass data
          productNdc: configuration.productNdc,
          packageNdc: configuration.packageNdc,
          regulatedProductName: configuration.regulatedProductName,
          manufacturerName: configuration.manufacturerName,
          dosageFormType: configuration.dosageFormType,
          strengthDescription: configuration.strengthDescription,
          netContentDescription: configuration.netContentDescription
        };
      }

      // Save serial numbers if we're on step 2 or beyond
      if (currentStep >= 2 && hierarchicalSerials) {
        updateData.serial_numbers = hierarchicalSerials;
      }

      await axios.put(`${API}/projects/${currentProject.id}`, updateData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (showToast) {
        setSuccess('Progress saved successfully!');
      }
      setHasUnsavedChanges(false);
    } catch (err) {
      if (showToast) {
        setError('Failed to save progress');
      }
      console.error('Error saving progress:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveAndExit = async () => {
    await handleSaveProgress();
    if (!error) {
      // Clear unsaved changes flag since we just saved
      setHasUnsavedChanges(false);
      handleBackToDashboard();
    }
  };

  const scrollToTop = () => {
    // Small delay to ensure the new step content is rendered
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 100);
  };

  // Auto-save functionality with debouncing
  const autoSave = async (showToast = false) => {
    if (!currentProject || isAutoSaving) return;

    try {
      setIsAutoSaving(true);
      await handleSaveProgress(false); // Pass false to prevent showing toast
      
      if (showToast) {
        setSuccess('Progress auto-saved');
      }
    } catch (err) {
      console.error('Auto-save failed:', err);
      // Don't show error toast for auto-save failures to avoid spam
    } finally {
      setIsAutoSaving(false);
    }
  };

  // Debounced auto-save function
  const debouncedAutoSave = (delay = 2000) => {
    // Clear existing timer
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }

    // Set new timer
    const newTimer = setTimeout(() => {
      autoSave();
    }, delay);

    setAutoSaveTimer(newTimer);
  };

  // Auto-save before exit to dashboard
  const autoSaveBeforeExit = async () => {
    if (!currentProject || !hasUnsavedChanges) return;

    try {
      setIsAutoSaving(true);
      await handleSaveProgress(false); // Save without showing toast
      setHasUnsavedChanges(false);
      setSuccess('Progress restored');
    } catch (err) {
      console.error('Auto-save before exit failed:', err);
      // Still proceed with exit, but show error
      setError('Failed to save progress before exit');
    } finally {
      setIsAutoSaving(false);
    }
  };

  // Initialize hierarchical serial collection structure
  // Smart initialization that preserves existing serial numbers when possible
  const initializeOrPreserveHierarchicalSerials = (config = configuration) => {
    const existingSerials = hierarchicalSerials;
    
    // If there are no existing serials, just initialize fresh
    if (!existingSerials || existingSerials.length === 0) {
      initializeHierarchicalSerials(config);
      return;
    }
    
    // If packaging configuration is locked, don't allow structural changes
    if (isPackagingConfigLocked && originalPackagingConfig) {
      // Check if structural packaging configuration has changed
      const structuralChangeDetected = 
        config.numberOfSscc !== originalPackagingConfig.numberOfSscc ||
        config.casesPerSscc !== originalPackagingConfig.casesPerSscc ||
        config.useInnerCases !== originalPackagingConfig.useInnerCases ||
        config.innerCasesPerCase !== originalPackagingConfig.innerCasesPerCase ||
        config.itemsPerCase !== originalPackagingConfig.itemsPerCase ||
        config.itemsPerInnerCase !== originalPackagingConfig.itemsPerInnerCase;
      
      if (structuralChangeDetected) {
        // Show error message and prevent changes
        setError(
          'Cannot modify Packaging Configuration after serial numbers have been entered. ' +
          'The current configuration has been restored. To make packaging changes, start a new project.'
        );
        
        // Restore original packaging configuration
        setConfiguration(prevConfig => ({
          ...prevConfig,
          itemsPerCase: originalPackagingConfig.itemsPerCase,
          casesPerSscc: originalPackagingConfig.casesPerSscc,
          numberOfSscc: originalPackagingConfig.numberOfSscc,
          useInnerCases: originalPackagingConfig.useInnerCases,
          innerCasesPerCase: originalPackagingConfig.innerCasesPerCase,
          itemsPerInnerCase: originalPackagingConfig.itemsPerInnerCase
        }));
        
        return false;
      }
    }
    
    // Configuration is allowed to change (either no lock or non-structural changes)
    return true;
  };

  const initializeHierarchicalSerials = (config = configuration) => {
    const hierarchicalData = [];
    
    // Parse configuration values to ensure they are numbers
    const numberOfSscc = parseInt(config.numberOfSscc) || 0;
    const casesPerSscc = parseInt(config.casesPerSscc) || 0;
    const itemsPerCase = parseInt(config.itemsPerCase) || 0;
    const innerCasesPerCase = parseInt(config.innerCasesPerCase) || 0;
    const itemsPerInnerCase = parseInt(config.itemsPerInnerCase) || 0;
    const useInnerCases = config.useInnerCases;
    
    console.log('initializeHierarchicalSerials - Configuration values:', {
      numberOfSscc,
      casesPerSscc,
      itemsPerCase,
      innerCasesPerCase,
      itemsPerInnerCase,
      useInnerCases
    });
    
    // Create structure based on configuration
    for (let ssccIndex = 0; ssccIndex < numberOfSscc; ssccIndex++) {
      const ssccData = {
        ssccIndex: ssccIndex,
        ssccSerial: '',
        cases: []
      };
      
      if (casesPerSscc === 0) {
        // Direct SSCC → Items
        ssccData.items = [];
        for (let itemIndex = 0; itemIndex < itemsPerCase; itemIndex++) {
          ssccData.items.push({
            itemIndex: itemIndex,
            itemSerial: ''
          });
        }
      } else {
        // SSCC → Cases → Items or SSCC → Cases → Inner Cases → Items
        for (let caseIndex = 0; caseIndex < casesPerSscc; caseIndex++) {
          const caseData = {
            caseIndex: caseIndex,
            caseSerial: '',
            innerCases: [],
            items: []
          };
          
          if (useInnerCases) {
            // Cases → Inner Cases → Items
            for (let innerCaseIndex = 0; innerCaseIndex < innerCasesPerCase; innerCaseIndex++) {
              const innerCaseData = {
                innerCaseIndex: innerCaseIndex,
                innerCaseSerial: '',
                items: []
              };
              
              for (let itemIndex = 0; itemIndex < itemsPerInnerCase; itemIndex++) {
                innerCaseData.items.push({
                  itemIndex: itemIndex,
                  itemSerial: ''
                });
              }
              
              caseData.innerCases.push(innerCaseData);
            }
          } else {
            // Cases → Items
            for (let itemIndex = 0; itemIndex < itemsPerCase; itemIndex++) {
              caseData.items.push({
                itemIndex: itemIndex,
                itemSerial: ''
              });
            }
          }
          
          ssccData.cases.push(caseData);
        }
      }
      
      hierarchicalData.push(ssccData);
    }
    
    console.log('initializeHierarchicalSerials - Generated structure:', hierarchicalData);
    
    setHierarchicalSerials(hierarchicalData);
    setSerialCollectionStep({
      ssccIndex: 0,
      caseIndex: 0,
      innerCaseIndex: 0,
      itemIndex: 0,
      currentLevel: 'sscc',
      currentSerial: '',
      isComplete: false
    });
  };

  const handleConfigurationSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    // Validate required fields
    const requiredFields = [
      { field: 'numberOfSscc', value: configuration.numberOfSscc, name: 'Number of SSCC' },
      { field: 'companyPrefix', value: configuration.companyPrefix, name: 'Company Prefix' },
      { field: 'productCode', value: configuration.productCode, name: 'Product Code' },
      { field: 'ssccExtensionDigit', value: configuration.ssccExtensionDigit, name: 'SSCC Extension Digit' },
      { field: 'caseIndicatorDigit', value: configuration.caseIndicatorDigit, name: 'Case Indicator Digit' },
      { field: 'itemIndicatorDigit', value: configuration.itemIndicatorDigit, name: 'Item Indicator Digit' }
    ];
    
    // Special validation for casesPerSscc - it can be 0 (for direct SSCC→Items) but not empty
    if (configuration.casesPerSscc === '' || configuration.casesPerSscc === null || configuration.casesPerSscc === undefined) {
      setError('Please fill in the following required fields: Cases per SSCC');
      setIsLoading(false);
      return;
    }
    
    const emptyFields = requiredFields.filter(field => !field.value || field.value === '');
    
    if (emptyFields.length > 0) {
      const fieldNames = emptyFields.map(field => field.name).join(', ');
      setError(`Please fill in the following required fields: ${fieldNames}`);
      setIsLoading(false);
      return;
    }
    
    // Additional validation for inner cases
    if (configuration.useInnerCases && configuration.casesPerSscc > 0) {
      if (!configuration.innerCaseIndicatorDigit || configuration.innerCaseIndicatorDigit === '') {
        setError('Please fill in the Inner Case Indicator Digit when using inner cases.');
        setIsLoading(false);
        return;
      }
    }
    
    try {
      const response = await axios.post(`${API}/projects/${currentProject.id}/configuration`, {
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
        sscc_extension_digit: configuration.ssccExtensionDigit,
        case_indicator_digit: configuration.caseIndicatorDigit,
        inner_case_indicator_digit: configuration.useInnerCases && configuration.casesPerSscc > 0 ? configuration.innerCaseIndicatorDigit : '',
        item_indicator_digit: configuration.itemIndicatorDigit,
        // Business Document Information
        sender_company_prefix: configuration.senderCompanyPrefix,
        sender_gln: configuration.senderGln,
        sender_sgln: configuration.senderSgln,
        sender_name: configuration.senderName,
        sender_street_address: configuration.senderStreetAddress,
        sender_city: configuration.senderCity,
        sender_state: configuration.senderState,
        sender_postal_code: configuration.senderPostalCode,
        sender_country_code: configuration.senderCountryCode,
        sender_despatch_advice_number: configuration.senderDespatchAdviceNumber,
        receiver_company_prefix: configuration.receiverCompanyPrefix,
        receiver_gln: configuration.receiverGln,
        receiver_sgln: configuration.receiverSgln,
        receiver_name: configuration.receiverName,
        receiver_street_address: configuration.receiverStreetAddress,
        receiver_city: configuration.receiverCity,
        receiver_state: configuration.receiverState,
        receiver_postal_code: configuration.receiverPostalCode,
        receiver_country_code: configuration.receiverCountryCode,
        receiver_po_number: configuration.receiverPoNumber,
        shipper_company_prefix: configuration.shipperCompanyPrefix,
        shipper_gln: configuration.shipperGln,
        shipper_sgln: configuration.shipperSgln,
        shipper_name: configuration.shipperName,
        shipper_street_address: configuration.shipperStreetAddress,
        shipper_city: configuration.shipperCity,
        shipper_state: configuration.shipperState,
        shipper_postal_code: configuration.shipperPostalCode,
        shipper_country_code: configuration.shipperCountryCode,
        shipper_same_as_sender: configuration.shipperSameAsSender,
        // EPCClass data
        product_ndc: configuration.productNdc,
        package_ndc: configuration.packageNdc,
        regulated_product_name: configuration.regulatedProductName,
        manufacturer_name: configuration.manufacturerName,
        dosage_form_type: configuration.dosageFormType,
        strength_description: configuration.strengthDescription,
        net_content_description: configuration.netContentDescription
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setConfigurationId(response.data.id);
      
      // Also save the complete configuration to the project for persistence
      await axios.put(`${API}/projects/${currentProject.id}`, {
        configuration: {
          itemsPerCase: configuration.itemsPerCase,
          casesPerSscc: configuration.casesPerSscc,
          numberOfSscc: configuration.numberOfSscc,
          useInnerCases: configuration.useInnerCases,
          innerCasesPerCase: configuration.innerCasesPerCase,
          itemsPerInnerCase: configuration.itemsPerInnerCase,
          companyPrefix: configuration.companyPrefix,
          productCode: configuration.productCode,
          lotNumber: configuration.lotNumber,
          expirationDate: configuration.expirationDate,
          ssccExtensionDigit: configuration.ssccExtensionDigit,
          caseIndicatorDigit: configuration.caseIndicatorDigit,
          innerCaseIndicatorDigit: configuration.innerCaseIndicatorDigit,
          itemIndicatorDigit: configuration.itemIndicatorDigit,
          // Business Document Information
          senderCompanyPrefix: configuration.senderCompanyPrefix,
          senderGln: configuration.senderGln,
          senderSgln: configuration.senderSgln,
          senderName: configuration.senderName,
          senderStreetAddress: configuration.senderStreetAddress,
          senderCity: configuration.senderCity,
          senderState: configuration.senderState,
          senderPostalCode: configuration.senderPostalCode,
          senderCountryCode: configuration.senderCountryCode,
          senderDespatchAdviceNumber: configuration.senderDespatchAdviceNumber,
          receiverCompanyPrefix: configuration.receiverCompanyPrefix,
          receiverGln: configuration.receiverGln,
          receiverSgln: configuration.receiverSgln,
          receiverName: configuration.receiverName,
          receiverStreetAddress: configuration.receiverStreetAddress,
          receiverCity: configuration.receiverCity,
          receiverState: configuration.receiverState,
          receiverPostalCode: configuration.receiverPostalCode,
          receiverCountryCode: configuration.receiverCountryCode,
          receiverPoNumber: configuration.receiverPoNumber,
          shipperCompanyPrefix: configuration.shipperCompanyPrefix,
          shipperGln: configuration.shipperGln,
          shipperSgln: configuration.shipperSgln,
          shipperName: configuration.shipperName,
          shipperStreetAddress: configuration.shipperStreetAddress,
          shipperCity: configuration.shipperCity,
          shipperState: configuration.shipperState,
          shipperPostalCode: configuration.shipperPostalCode,
          shipperCountryCode: configuration.shipperCountryCode,
          shipperSameAsSender: configuration.shipperSameAsSender,
          // EPCClass data
          productNdc: configuration.productNdc,
          packageNdc: configuration.packageNdc,
          regulatedProductName: configuration.regulatedProductName,
          manufacturerName: configuration.manufacturerName,
          dosageFormType: configuration.dosageFormType,
          strengthDescription: configuration.strengthDescription,
          netContentDescription: configuration.netContentDescription
        },
        current_step: 2,
        updated_at: new Date().toISOString()
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Initialize hierarchical serial collection (preserve existing if possible)
      const shouldContinue = initializeOrPreserveHierarchicalSerials();
      
      if (shouldContinue === false) {
        // Configuration change was blocked or user cancelled
        setIsLoading(false);
        return;
      }
      
      // Lock packaging configuration if we have serial numbers
      if (hierarchicalSerials && hierarchicalSerials.length > 0) {
        setIsPackagingConfigLocked(true);
        setOriginalPackagingConfig({
          itemsPerCase: configuration.itemsPerCase,
          casesPerSscc: configuration.casesPerSscc,
          numberOfSscc: configuration.numberOfSscc,
          useInnerCases: configuration.useInnerCases,
          innerCasesPerCase: configuration.innerCasesPerCase,
          itemsPerInnerCase: configuration.itemsPerInnerCase
        });
      }
      
      // CRITICAL: On mobile, React state updates can be asynchronous and cause race conditions
      // Force synchronous state clearing before checking hierarchicalSerials
      setHierarchicalSerials([]);
      
      // Wait for state update to complete on mobile devices
      await new Promise(resolve => setTimeout(resolve, 0));
      
      // If we have existing serial numbers, auto-save them with the new configuration
      // But since we just cleared the state, this should only apply to projects with saved data
      if (currentProject && currentProject.serial_numbers && currentProject.serial_numbers.length > 0) {
        // Restore and auto-save existing project data
        setHierarchicalSerials(currentProject.serial_numbers);
        autoSaveSerialNumbers(currentProject.serial_numbers);
        console.log('Preserved existing project serial data');
      } else {
        // For new projects or projects without serial data, initialize the hierarchical structure
        // based on the configuration they just set up
        console.log('Initializing empty hierarchical serials for new project configuration');
        initializeHierarchicalSerials(configuration);
      }
      
      // Navigate to step 2
      setCurrentStep(2);
      
      // Set appropriate success message
      if (hierarchicalSerials && hierarchicalSerials.length > 0) {
        setSuccess('Configuration saved successfully! Your previously entered serial numbers have been preserved.');
      } else {
        setSuccess('Configuration saved successfully! Ready to assign serial numbers.');
      }
      
      scrollToTop();
    } catch (err) {
      setError('Failed to save configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSerialNumbersSubmit = async () => {
    console.log('Submitting serial numbers. Current hierarchicalSerials:', hierarchicalSerials);
    
    // Add safety check for hierarchicalSerials
    if (!hierarchicalSerials || !Array.isArray(hierarchicalSerials)) {
      console.error('hierarchicalSerials is undefined or not an array:', hierarchicalSerials);
      setError('Serial numbers data is missing. Please reload the project and try again.');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      // Convert hierarchical structure to flat arrays for backend
      const ssccArray = [];
      const caseArray = [];
      const innerCaseArray = [];
      const itemArray = [];
      
      hierarchicalSerials.forEach(ssccData => {
        ssccArray.push(ssccData.ssccSerial);
        
        if (ssccData.cases && ssccData.cases.length > 0) {
          // Has cases
          ssccData.cases.forEach(caseData => {
            caseArray.push(caseData.caseSerial);
            
            if (caseData.innerCases && caseData.innerCases.length > 0) {
              // Has inner cases
              caseData.innerCases.forEach(innerCaseData => {
                innerCaseArray.push(innerCaseData.innerCaseSerial);
                innerCaseData.items.forEach(itemData => {
                  itemArray.push(itemData.itemSerial);
                });
              });
            } else {
              // Direct case → items
              caseData.items.forEach(itemData => {
                itemArray.push(itemData.itemSerial);
              });
            }
          });
        } else {
          // Direct SSCC → items
          ssccData.items.forEach(itemData => {
            itemArray.push(itemData.itemSerial);
          });
        }
      });
      
      await axios.post(`${API}/projects/${currentProject.id}/serial-numbers`, {
        sscc_serial_numbers: ssccArray,
        case_serial_numbers: caseArray,
        inner_case_serial_numbers: innerCaseArray,
        item_serial_numbers: itemArray
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Navigate to step 3
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
      const response = await axios.post(`${API}/projects/${currentProject.id}/generate-epcis`, {
        read_point: "urn:epc:id:sgln:1234567.00000.0",
        biz_location: "urn:epc:id:sgln:1234567.00001.0"
      }, {
        responseType: 'blob',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from Content-Disposition header, fallback to default if not present
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'epcis_aggregation.xml'; // fallback
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      link.setAttribute('download', filename);
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

  const handleStepClick = async (step) => {
    if (step < currentStep) {
      // Auto-save before navigation
      if (hasUnsavedChanges) {
        await autoSave();
      }
      
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
      companyPrefix: '',
      productCode: '',
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
    // Reset hierarchical serial collection state
    setHierarchicalSerials([]);
    setSerialCollectionStep({
      ssccIndex: 0,
      caseIndex: 0,
      innerCaseIndex: 0,
      itemIndex: 0,
      currentLevel: 'sscc',
      currentSerial: '',
      isComplete: false
    });
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

  // Duplicate validation function
  const validateDuplicateSerials = (newSerial, currentPath, excludePaths = []) => {
    const allSerials = [];
    
    // Normalize the serial number (trim whitespace, convert to lowercase for comparison)
    const normalizedNewSerial = newSerial.trim().toLowerCase();
    
    console.log('validateDuplicateSerials called with:', {
      newSerial,
      normalizedNewSerial,
      currentPath,
      excludePaths,
      hierarchicalSerialsLength: hierarchicalSerials.length
    });
    
    if (!normalizedNewSerial) {
      return null; // Empty serials are not duplicates
    }
    
    // Collect all existing serials
    hierarchicalSerials.forEach((ssccData, ssccIndex) => {
      console.log(`Processing SSCC ${ssccIndex}:`, ssccData);
      
      if (ssccData.ssccSerial && ssccData.ssccSerial.trim()) {
        allSerials.push({
          serial: ssccData.ssccSerial.trim(),
          normalizedSerial: ssccData.ssccSerial.trim().toLowerCase(),
          path: `SSCC ${ssccIndex + 1}`,
          isCurrentPath: currentPath === `sscc-${ssccIndex}`
        });
      }
      
      if (ssccData.cases) {
        ssccData.cases.forEach((caseData, caseIndex) => {
          console.log(`Processing Case ${caseIndex}:`, caseData);
          
          if (caseData.caseSerial && caseData.caseSerial.trim()) {
            allSerials.push({
              serial: caseData.caseSerial.trim(),
              normalizedSerial: caseData.caseSerial.trim().toLowerCase(),
              path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1}`,
              isCurrentPath: currentPath === `case-${ssccIndex}-${caseIndex}`
            });
          }
          
          if (caseData.innerCases && caseData.innerCases.length > 0) {
            console.log(`Case ${caseIndex} has innerCases:`, caseData.innerCases);
            caseData.innerCases.forEach((innerCaseData, innerCaseIndex) => {
              if (innerCaseData.innerCaseSerial && innerCaseData.innerCaseSerial.trim()) {
                allSerials.push({
                  serial: innerCaseData.innerCaseSerial.trim(),
                  normalizedSerial: innerCaseData.innerCaseSerial.trim().toLowerCase(),
                  path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1} → Inner Case ${innerCaseIndex + 1}`,
                  isCurrentPath: currentPath === `innerCase-${ssccIndex}-${caseIndex}-${innerCaseIndex}`
                });
              }
              
              if (innerCaseData.items) {
                console.log(`Inner Case ${innerCaseIndex} has items:`, innerCaseData.items);
                innerCaseData.items.forEach((itemData, itemIndex) => {
                  if (itemData.itemSerial && itemData.itemSerial.trim()) {
                    allSerials.push({
                      serial: itemData.itemSerial.trim(),
                      normalizedSerial: itemData.itemSerial.trim().toLowerCase(),
                      path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1} → Inner Case ${innerCaseIndex + 1} → Item ${itemIndex + 1}`,
                      isCurrentPath: currentPath === `item-${ssccIndex}-${caseIndex}-${innerCaseIndex}-${itemIndex}`
                    });
                  }
                });
              }
            });
          } else if (caseData.items) {
            console.log(`Case ${caseIndex} has items:`, caseData.items);
            caseData.items.forEach((itemData, itemIndex) => {
              console.log(`Processing item ${itemIndex}:`, itemData);
              if (itemData.itemSerial && itemData.itemSerial.trim()) {
                console.log(`Adding item serial: ${itemData.itemSerial}`);
                allSerials.push({
                  serial: itemData.itemSerial.trim(),
                  normalizedSerial: itemData.itemSerial.trim().toLowerCase(),
                  path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1} → Item ${itemIndex + 1}`,
                  isCurrentPath: currentPath === `item-${ssccIndex}-${caseIndex}-${itemIndex}`
                });
              } else {
                console.log(`Item ${itemIndex} has no itemSerial or empty:`, itemData.itemSerial);
              }
            });
          } else {
            console.log(`Case ${caseIndex} has no items or innerCases`);
          }
        });
      } else if (ssccData.items) {
        ssccData.items.forEach((itemData, itemIndex) => {
          if (itemData.itemSerial && itemData.itemSerial.trim()) {
            allSerials.push({
              serial: itemData.itemSerial.trim(),
              normalizedSerial: itemData.itemSerial.trim().toLowerCase(),
              path: `SSCC ${ssccIndex + 1} → Item ${itemIndex + 1}`,
              isCurrentPath: currentPath === `item-${ssccIndex}-${itemIndex}`
            });
          }
        });
      }
    });
    
    console.log('All serials collected:', allSerials);
    console.log('Looking for normalized serial:', normalizedNewSerial);
    
    // Check for duplicates using normalized comparison, excluding current path and excluded paths
    const duplicates = allSerials.filter(item => {
      const isCurrentPath = item.isCurrentPath;
      
      // Check if this item's path is in the exclude list
      // Extract path format from the collected serial item and compare with exclude paths
      let itemPath = '';
      if (item.path.includes('Inner Case')) {
        // Extract indices for inner case items: "SSCC 1 → Case 1 → Inner Case 1 → Item 1" 
        const matches = item.path.match(/SSCC (\d+).*Case (\d+).*Inner Case (\d+).*Item (\d+)/);
        if (matches) {
          const [, sscc, case_, innerCase, itemNum] = matches;
          itemPath = `item-${parseInt(sscc)-1}-${parseInt(case_)-1}-${parseInt(innerCase)-1}-${parseInt(itemNum)-1}`;
        }
      } else if (item.path.includes('→ Case')) {
        // Extract indices for case items: "SSCC 1 → Case 1 → Item 1"
        const matches = item.path.match(/SSCC (\d+).*Case (\d+).*Item (\d+)/);
        if (matches) {
          const [, sscc, case_, itemNum] = matches;
          itemPath = `item-${parseInt(sscc)-1}-${parseInt(case_)-1}-${parseInt(itemNum)-1}`;
        }
      } else if (item.path.includes('→ Item')) {
        // Extract indices for direct items: "SSCC 1 → Item 1"
        const matches = item.path.match(/SSCC (\d+).*Item (\d+)/);
        if (matches) {
          const [, sscc, itemNum] = matches;
          itemPath = `item-${parseInt(sscc)-1}-${parseInt(itemNum)-1}`;
        }
      }
      
      const isExcludedPath = excludePaths.includes(itemPath);
      
      return item.normalizedSerial === normalizedNewSerial && !isCurrentPath && !isExcludedPath;
    });
    
    console.log('Duplicates found:', duplicates);
    
    return duplicates.length > 0 ? duplicates : null;
  };

  // Hierarchical serial number functions
  // Hierarchical serial number functions
  const handleSerialInput = (value) => {
    // Check for duplicates
    if (serialCollectionStep.currentLevel === 'item' && value.includes('\n')) {
      // Multi-line item input - check each line
      const serialLines = value.split('\n');
      let hasError = false;
      
      for (let i = 0; i < serialLines.length; i++) {
        const serial = serialLines[i].trim();
        if (serial) {
          // Create a temporary path for this specific item index
          const tempItemIndex = serialCollectionStep.itemIndex + i;
          let tempPath;
          if (configuration.useInnerCases) {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${serialCollectionStep.innerCaseIndex}-${tempItemIndex}`;
          } else if (configuration.casesPerSscc > 0) {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${tempItemIndex}`;
          } else {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${tempItemIndex}`;
          }
          
          // Check for duplicates against existing serials
          const duplicates = validateDuplicateSerials(serial, tempPath);
          if (duplicates) {
            setError(`Duplicate serial number found on line ${i + 1}! "${serial}" is already used at: ${duplicates[0].path}`);
            hasError = true;
            break;
          }
          
          // Also check for duplicates within the current input (case-insensitive)
          for (let j = 0; j < i; j++) {
            const previousSerial = serialLines[j].trim();
            if (previousSerial && previousSerial.toLowerCase() === serial.toLowerCase()) {
              setError(`Duplicate serial number found on line ${i + 1}! "${serial}" is already used on line ${j + 1} in this input.`);
              hasError = true;
              break;
            }
          }
          
          if (hasError) break;
        }
      }
      
      if (!hasError) {
        setError('');
      }
    } else {
      // Single line input - check for duplicates
      const currentPath = getCurrentPath();
      const duplicates = validateDuplicateSerials(value, currentPath);
      
      if (duplicates && value.trim()) {
        setError(`Duplicate serial number found! "${value}" is already used at: ${duplicates[0].path}`);
      } else {
        setError('');
      }
    }
    
    setSerialCollectionStep({
      ...serialCollectionStep,
      currentSerial: value
    });
  };

  const getCurrentPath = () => {
    const step = serialCollectionStep;
    switch (step.currentLevel) {
      case 'sscc':
        return `sscc-${step.ssccIndex}`;
      case 'case':
        return `case-${step.ssccIndex}-${step.caseIndex}`;
      case 'innerCase':
        return `innerCase-${step.ssccIndex}-${step.caseIndex}-${step.innerCaseIndex}`;
      case 'item':
        if (configuration.useInnerCases) {
          return `item-${step.ssccIndex}-${step.caseIndex}-${step.innerCaseIndex}-${step.itemIndex}`;
        } else if (configuration.casesPerSscc > 0) {
          return `item-${step.ssccIndex}-${step.caseIndex}-${step.itemIndex}`;
        } else {
          return `item-${step.ssccIndex}-${step.itemIndex}`;
        }
      default:
        return '';
    }
  };

  const handleEditSerial = (path, currentValue) => {
    const pathParts = path.split('-');
    const level = pathParts[0];
    const ssccIndex = parseInt(pathParts[1]);
    const caseIndex = pathParts[2] ? parseInt(pathParts[2]) : 0;
    const innerCaseIndex = pathParts[3] ? parseInt(pathParts[3]) : 0;
    const itemIndex = pathParts[4] ? parseInt(pathParts[4]) : (pathParts[3] ? parseInt(pathParts[3]) : 0);
    
    // Generate context path and label
    const ssccNum = ssccIndex + 1;
    const caseNum = caseIndex + 1;
    const innerCaseNum = innerCaseIndex + 1;
    const itemNum = itemIndex + 1;
    
    let contextPath = '';
    let label = '';
    
    switch (level) {
      case 'sscc':
        contextPath = `SSCC ${ssccNum}`;
        label = 'SSCC Serial Number';
        break;
      case 'case':
        contextPath = `SSCC ${ssccNum} → Case ${caseNum}`;
        label = 'Case Serial Number';
        break;
      case 'innerCase':
        contextPath = `SSCC ${ssccNum} → Case ${caseNum} → Inner Case ${innerCaseNum}`;
        label = 'Inner Case Serial Number';
        break;
      case 'item':
        if (configuration.useInnerCases) {
          contextPath = `SSCC ${ssccNum} → Case ${caseNum} → Inner Case ${innerCaseNum} → Item ${itemNum}`;
        } else if (configuration.casesPerSscc > 0) {
          contextPath = `SSCC ${ssccNum} → Case ${caseNum} → Item ${itemNum}`;
        } else {
          contextPath = `SSCC ${ssccNum} → Item ${itemNum}`;
        }
        label = 'Item Serial Number';
        break;
    }
    
    setEditModal({
      isOpen: true,
      path: path,
      currentValue: currentValue || '',
      label: label,
      contextPath: contextPath
    });
  };

  const handleSaveEditedSerial = () => {
    if (!editModal.currentValue.trim()) {
      setError('Please enter a serial number');
      return;
    }

    // Check for duplicates
    const duplicates = validateDuplicateSerials(editModal.currentValue, editModal.path);
    
    if (duplicates) {
      setError(`Duplicate serial number found! "${editModal.currentValue}" is already used at: ${duplicates[0].path}`);
      return;
    }

    // Save the edited serial
    const pathParts = editModal.path.split('-');
    const level = pathParts[0];
    const ssccIndex = parseInt(pathParts[1]);
    const caseIndex = pathParts[2] ? parseInt(pathParts[2]) : 0;
    const innerCaseIndex = pathParts[3] ? parseInt(pathParts[3]) : 0;
    const itemIndex = pathParts[4] ? parseInt(pathParts[4]) : (pathParts[3] ? parseInt(pathParts[3]) : 0);
    
    const updatedSerials = [...hierarchicalSerials];
    const currentSSCC = updatedSerials[ssccIndex];
    
    switch (level) {
      case 'sscc':
        currentSSCC.ssccSerial = editModal.currentValue;
        break;
      case 'case':
        currentSSCC.cases[caseIndex].caseSerial = editModal.currentValue;
        break;
      case 'innerCase':
        currentSSCC.cases[caseIndex].innerCases[innerCaseIndex].innerCaseSerial = editModal.currentValue;
        break;
      case 'item':
        if (configuration.useInnerCases) {
          currentSSCC.cases[caseIndex].innerCases[innerCaseIndex].items[itemIndex].itemSerial = editModal.currentValue;
        } else if (configuration.casesPerSscc > 0) {
          currentSSCC.cases[caseIndex].items[itemIndex].itemSerial = editModal.currentValue;
        } else {
          currentSSCC.items[itemIndex].itemSerial = editModal.currentValue;
        }
        break;
    }
    
    setHierarchicalSerials(updatedSerials);
    
    // Auto-save serial numbers
    autoSaveSerialNumbers(updatedSerials);
    
    setEditModal({ isOpen: false, path: '', currentValue: '', label: '', contextPath: '' });
    setError('');
    setSuccess('Serial number updated successfully!');
  };

  const handleCancelEdit = () => {
    setEditModal({ isOpen: false, path: '', currentValue: '', label: '', contextPath: '' });
    setError('');
  };

  const renderClickableContext = (contextPath) => {
    const pathParts = contextPath.split(' → ');
    
    return pathParts.map((part, index) => {
      const isLast = index === pathParts.length - 1;
      
      return (
        <span key={index}>
          <span
            className={`context-level ${isLast ? 'context-current' : 'context-clickable'}`}
            onClick={() => {
              if (!isLast) {
                handleContextNavigation(part, index);
              }
            }}
          >
            {part}
          </span>
          {!isLast && <span className="context-separator"> → </span>}
        </span>
      );
    });
  };

  const handleContextNavigation = (clickedLevel, levelIndex) => {
    // Get current hierarchical data before making any changes
    const currentHierarchicalData = [...hierarchicalSerials];
    
    // Save current serial before navigating (but preserve all existing data)
    if (serialCollectionStep.currentSerial.trim()) {
      const currentSSCC = currentHierarchicalData[serialCollectionStep.ssccIndex];
      
      switch (serialCollectionStep.currentLevel) {
        case 'sscc':
          currentSSCC.ssccSerial = serialCollectionStep.currentSerial;
          break;
        case 'case':
          if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex]) {
            currentSSCC.cases[serialCollectionStep.caseIndex].caseSerial = serialCollectionStep.currentSerial;
          }
          break;
        case 'innerCase':
          if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex]) {
            currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].innerCaseSerial = serialCollectionStep.currentSerial;
          }
          break;
        case 'item':
          // For items, handle both single and multi-line
          if (serialCollectionStep.currentSerial.includes('\n')) {
            // Multi-line handling
            const serialLines = serialCollectionStep.currentSerial.split('\n').filter(line => line.trim());
            for (let i = 0; i < serialLines.length; i++) {
              const serial = serialLines[i].trim();
              if (serial) {
                const currentItemIndex = serialCollectionStep.itemIndex + i;
                if (configuration.useInnerCases) {
                  if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items[currentItemIndex]) {
                    currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items[currentItemIndex].itemSerial = serial;
                  }
                } else if (configuration.casesPerSscc > 0) {
                  if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].items && currentSSCC.cases[serialCollectionStep.caseIndex].items[currentItemIndex]) {
                    currentSSCC.cases[serialCollectionStep.caseIndex].items[currentItemIndex].itemSerial = serial;
                  }
                } else {
                  if (currentSSCC.items && currentSSCC.items[currentItemIndex]) {
                    currentSSCC.items[currentItemIndex].itemSerial = serial;
                  }
                }
              }
            }
          } else {
            // Single line handling
            if (configuration.useInnerCases) {
              if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items && currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items[serialCollectionStep.itemIndex]) {
                currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items[serialCollectionStep.itemIndex].itemSerial = serialCollectionStep.currentSerial;
              }
            } else if (configuration.casesPerSscc > 0) {
              if (currentSSCC.cases && currentSSCC.cases[serialCollectionStep.caseIndex] && currentSSCC.cases[serialCollectionStep.caseIndex].items && currentSSCC.cases[serialCollectionStep.caseIndex].items[serialCollectionStep.itemIndex]) {
                currentSSCC.cases[serialCollectionStep.caseIndex].items[serialCollectionStep.itemIndex].itemSerial = serialCollectionStep.currentSerial;
              }
            } else {
              if (currentSSCC.items && currentSSCC.items[serialCollectionStep.itemIndex]) {
                currentSSCC.items[serialCollectionStep.itemIndex].itemSerial = serialCollectionStep.currentSerial;
              }
            }
          }
          break;
      }
    }
    
    // CRITICAL: Update hierarchical data BEFORE changing navigation state
    // This ensures all previous serial numbers are preserved
    setHierarchicalSerials(currentHierarchicalData);
    
    // Helper function to find next unfinished item index
    const findNextItemIndex = (ssccIndex, caseIndex, innerCaseIndex) => {
      const sscc = currentHierarchicalData[ssccIndex];
      if (!sscc) return 0;
      
      if (configuration.useInnerCases) {
        const innerCase = sscc.cases?.[caseIndex]?.innerCases?.[innerCaseIndex];
        if (!innerCase?.items) return 0;
        
        for (let i = 0; i < innerCase.items.length; i++) {
          if (!innerCase.items[i].itemSerial) {
            return i;
          }
        }
        return innerCase.items.length;
      } else if (configuration.casesPerSscc > 0) {
        const caseData = sscc.cases?.[caseIndex];
        if (!caseData?.items) return 0;
        
        for (let i = 0; i < caseData.items.length; i++) {
          if (!caseData.items[i].itemSerial) {
            return i;
          }
        }
        return caseData.items.length;
      } else {
        if (!sscc.items) return 0;
        
        for (let i = 0; i < sscc.items.length; i++) {
          if (!sscc.items[i].itemSerial) {
            return i;
          }
        }
        return sscc.items.length;
      }
    };
    
    // Parse the clicked level to determine position and restore previous value
    const step = serialCollectionStep;
    
    if (clickedLevel.includes('SSCC')) {
      // Navigate to SSCC level - preserve all existing data
      const currentSSCC = currentHierarchicalData[step.ssccIndex];
      setSerialCollectionStep({
        ...step,
        currentLevel: 'sscc',
        currentSerial: currentSSCC.ssccSerial || '',
        // Don't reset indices - preserve current navigation context  
        isComplete: false
      });
    } else if (clickedLevel.includes('Case') && !clickedLevel.includes('Inner')) {
      // Navigate to Case level
      const currentCase = currentHierarchicalData[step.ssccIndex].cases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex];
      
      // Calculate the correct item index for this case
      const nextItemIndex = findNextItemIndex(step.ssccIndex, step.caseIndex, step.innerCaseIndex);
      
      setSerialCollectionStep({
        ...step,
        currentLevel: 'case',
        currentSerial: currentCase ? (currentCase.caseSerial || '') : '',
        innerCaseIndex: 0,
        itemIndex: nextItemIndex,
        isComplete: false
      });
    } else if (clickedLevel.includes('Inner Case')) {
      // Navigate to Inner Case level
      const currentInnerCase = currentHierarchicalData[step.ssccIndex].cases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex] && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex].innerCases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex].innerCases[step.innerCaseIndex];
      
      // Calculate the correct item index for this inner case
      const nextItemIndex = findNextItemIndex(step.ssccIndex, step.caseIndex, step.innerCaseIndex);
      
      setSerialCollectionStep({
        ...step,
        currentLevel: 'innerCase',
        currentSerial: currentInnerCase ? (currentInnerCase.innerCaseSerial || '') : '',
        itemIndex: nextItemIndex,
        isComplete: false
      });
    }
  };

  const handleNextSerial = () => {
    if (!serialCollectionStep.currentSerial.trim()) {
      setError('Please enter a serial number');
      return;
    }

    // Handle multiple serials for items
    if (serialCollectionStep.currentLevel === 'item') {
      const serialLines = serialCollectionStep.currentSerial.split('\n').filter(line => line.trim());
      
      // Validate all serials for duplicates, excluding current items being edited
      const currentItemPaths = [];
      for (let i = 0; i < serialLines.length; i++) {
        const tempItemIndex = serialCollectionStep.itemIndex + i;
        let tempPath;
        if (configuration.useInnerCases) {
          tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${serialCollectionStep.innerCaseIndex}-${tempItemIndex}`;
        } else if (configuration.casesPerSscc > 0) {
          tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${tempItemIndex}`;
        } else {
          tempPath = `item-${serialCollectionStep.ssccIndex}-${tempItemIndex}`;
        }
        currentItemPaths.push(tempPath);
      }
      
      for (let i = 0; i < serialLines.length; i++) {
        const serial = serialLines[i].trim();
        if (serial) {
          // Create a temporary path for this specific item index
          const tempItemIndex = serialCollectionStep.itemIndex + i;
          let tempPath;
          if (configuration.useInnerCases) {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${serialCollectionStep.innerCaseIndex}-${tempItemIndex}`;
          } else if (configuration.casesPerSscc > 0) {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${serialCollectionStep.caseIndex}-${tempItemIndex}`;
          } else {
            tempPath = `item-${serialCollectionStep.ssccIndex}-${tempItemIndex}`;
          }
          
          const duplicates = validateDuplicateSerials(serial, tempPath, currentItemPaths);
          if (duplicates) {
            setError(`Duplicate serial number found on line ${i + 1}! "${serial}" is already used at: ${duplicates[0].path}`);
            return;
          }
          
          // Also check for duplicates within the current input (case-insensitive)
          for (let j = 0; j < i; j++) {
            const previousSerial = serialLines[j].trim();
            if (previousSerial.toLowerCase() === serial.toLowerCase()) {
              setError(`Duplicate serial number found on line ${i + 1}! "${serial}" is already used on line ${j + 1} in this input.`);
              return;
            }
          }
        }
      }
      
      // Save multiple serials
      const updatedSerials = [...hierarchicalSerials];
      const currentSSCC = updatedSerials[serialCollectionStep.ssccIndex];
      
      for (let i = 0; i < serialLines.length; i++) {
        const serial = serialLines[i].trim();
        if (serial) {
          const currentItemIndex = serialCollectionStep.itemIndex + i;
          
          // Check if we have enough item slots
          let totalItemsInContainer;
          if (configuration.useInnerCases) {
            totalItemsInContainer = configuration.itemsPerInnerCase;
          } else if (configuration.casesPerSscc > 0) {
            totalItemsInContainer = configuration.itemsPerCase;
          } else {
            totalItemsInContainer = configuration.itemsPerCase;
          }
          
          if (currentItemIndex >= totalItemsInContainer) {
            setError(`Too many serial numbers entered. Maximum ${totalItemsInContainer} items allowed for this container.`);
            return;
          }
          
          // Save the serial
          if (configuration.useInnerCases) {
            currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].items[currentItemIndex].itemSerial = serial;
          } else if (configuration.casesPerSscc > 0) {
            currentSSCC.cases[serialCollectionStep.caseIndex].items[currentItemIndex].itemSerial = serial;
          } else {
            currentSSCC.items[currentItemIndex].itemSerial = serial;
          }
        }
      }
      
      setHierarchicalSerials(updatedSerials);
      
      // Auto-save serial numbers
      autoSaveSerialNumbers(updatedSerials);
      
      // Move to next step, accounting for multiple serials added
      const nextStep = calculateNextStep(serialLines.length - 1);
      setSerialCollectionStep({
        ...nextStep,
        // Only clear serial when transitioning FROM item level to new containers
        // Preserve serials when going TO item level (existing serials) or between non-item levels
        currentSerial: (serialCollectionStep.currentLevel === 'item' && nextStep.currentLevel !== 'item') 
          ? '' 
          : (nextStep.currentSerial || '')
      });
    } else {
      // Single serial handling for non-item levels
      const currentPath = getCurrentPath();
      const duplicates = validateDuplicateSerials(serialCollectionStep.currentSerial, currentPath);
      
      if (duplicates) {
        setError(`Duplicate serial number found! "${serialCollectionStep.currentSerial}" is already used at: ${duplicates[0].path}`);
        return;
      }

      // Save current serial and move to next
      const updatedSerials = [...hierarchicalSerials];
      const currentSSCC = updatedSerials[serialCollectionStep.ssccIndex];
      
      switch (serialCollectionStep.currentLevel) {
        case 'sscc':
          currentSSCC.ssccSerial = serialCollectionStep.currentSerial;
          break;
        case 'case':
          currentSSCC.cases[serialCollectionStep.caseIndex].caseSerial = serialCollectionStep.currentSerial;
          break;
        case 'innerCase':
          currentSSCC.cases[serialCollectionStep.caseIndex].innerCases[serialCollectionStep.innerCaseIndex].innerCaseSerial = serialCollectionStep.currentSerial;
          break;
      }
      
      setHierarchicalSerials(updatedSerials);
      
      // Auto-save serial numbers
      autoSaveSerialNumbers(updatedSerials);
      
      // Calculate next step
      const nextStep = calculateNextStep();
      setSerialCollectionStep({
        ...nextStep,
        // Only clear serial when transitioning FROM item level to new containers
        // Preserve serials when going TO item level (existing serials) or between non-item levels
        currentSerial: (serialCollectionStep.currentLevel === 'item' && nextStep.currentLevel !== 'item') 
          ? '' 
          : (nextStep.currentSerial || '')
      });
    }
    
    setError('');
  };

  const calculateNextStep = (itemsToSkip = 0) => {
    const current = serialCollectionStep;
    const totals = calculateTotals();
    
    // Helper function to find next unfinished item index
    const findNextItemIndex = (ssccIndex, caseIndex, innerCaseIndex) => {
      const sscc = hierarchicalSerials[ssccIndex];
      if (!sscc) return 0;
      
      if (configuration.useInnerCases) {
        const innerCase = sscc.cases?.[caseIndex]?.innerCases?.[innerCaseIndex];
        if (!innerCase?.items) return 0;
        
        for (let i = 0; i < innerCase.items.length; i++) {
          if (!innerCase.items[i].itemSerial) {
            return i;
          }
        }
        return innerCase.items.length;
      } else if (configuration.casesPerSscc > 0) {
        const caseData = sscc.cases?.[caseIndex];
        if (!caseData?.items) return 0;
        
        for (let i = 0; i < caseData.items.length; i++) {
          if (!caseData.items[i].itemSerial) {
            return i;
          }
        }
        return caseData.items.length;
      } else {
        if (!sscc.items) return 0;
        
        for (let i = 0; i < sscc.items.length; i++) {
          if (!sscc.items[i].itemSerial) {
            return i;
          }
        }
        return sscc.items.length;
      }
    };
    
    if (current.currentLevel === 'sscc') {
      // Move to the current case or first item (if direct SSCC→Items)
      if (configuration.casesPerSscc === 0) {
        // Direct SSCC → Items: Load existing item serials if they exist
        const currentSSCC = hierarchicalSerials[current.ssccIndex];
        const existingItems = currentSSCC?.items || [];
        
        // Build array of existing serials, preserving order and including empty slots
        const allSerials = [];
        for (let i = 0; i < configuration.itemsPerCase; i++) {
          const item = existingItems[i];
          const serial = item?.itemSerial || '';
          if (serial.trim()) {
            allSerials.push(serial);
          }
        }
        
        const existingSerials = allSerials.join('\n');
        const completedCount = allSerials.length;
        
        // If all items exist, start editing from index 0. Otherwise, continue from where left off
        const allItemsExist = completedCount === configuration.itemsPerCase;
        const itemIndex = allItemsExist ? 0 : completedCount;
        
        return {
          ...current,
          currentLevel: 'item',
          itemIndex: itemIndex,
          currentSerial: existingSerials
        };
      } else {
        // Continue with the case they were working on, and load its existing serial
        const currentSSCC = hierarchicalSerials[current.ssccIndex];
        const currentCase = currentSSCC?.cases?.[current.caseIndex];
        return {
          ...current,
          currentLevel: 'case',
          currentSerial: currentCase?.caseSerial || ''
          // Preserve current.caseIndex - don't reset it
        };
      }
    } else if (current.currentLevel === 'case') {
      // Move to the current inner case or first item
      if (configuration.useInnerCases) {
        // Continue with the inner case they were working on, and load its existing serial
        const currentSSCC = hierarchicalSerials[current.ssccIndex];
        const currentInnerCase = currentSSCC?.cases?.[current.caseIndex]?.innerCases?.[current.innerCaseIndex];
        return {
          ...current,
          currentLevel: 'innerCase',
          currentSerial: currentInnerCase?.innerCaseSerial || ''
          // Preserve current.innerCaseIndex - don't reset it
        };
      } else {
        // Load existing item serials if they exist when transitioning to items
        const currentSSCC = hierarchicalSerials[current.ssccIndex];
        const existingItems = currentSSCC?.cases?.[current.caseIndex]?.items || [];
        
        // Build array of existing serials, preserving order and including empty slots
        const allSerials = [];
        for (let i = 0; i < configuration.itemsPerCase; i++) {
          const item = existingItems[i];
          const serial = item?.itemSerial || '';
          if (serial.trim()) {
            allSerials.push(serial);
          }
        }
        
        const existingSerials = allSerials.join('\n');
        const completedCount = allSerials.length;
        
        // If all items exist, start editing from index 0. Otherwise, continue from where left off
        const allItemsExist = completedCount === configuration.itemsPerCase;
        const itemIndex = allItemsExist ? 0 : completedCount;
        
        return {
          ...current,
          currentLevel: 'item',
          itemIndex: itemIndex,
          currentSerial: existingSerials
        };
      }
    } else if (current.currentLevel === 'innerCase') {
      // Move to items in this inner case and load existing serials if they exist
      const currentSSCC = hierarchicalSerials[current.ssccIndex];
      const existingItems = currentSSCC?.cases?.[current.caseIndex]?.innerCases?.[current.innerCaseIndex]?.items || [];
      
      // Build array of existing serials, preserving order and including empty slots
      const allSerials = [];
      for (let i = 0; i < configuration.itemsPerInnerCase; i++) {
        const item = existingItems[i];
        const serial = item?.itemSerial || '';
        if (serial.trim()) {
          allSerials.push(serial);
        }
      }
      
      const existingSerials = allSerials.join('\n');
      const completedCount = allSerials.length;
      
      // If all items exist, start editing from index 0. Otherwise, continue from where left off
      const allItemsExist = completedCount === configuration.itemsPerInnerCase;
      const itemIndex = allItemsExist ? 0 : completedCount;
      
      return {
        ...current,
        currentLevel: 'item',
        itemIndex: itemIndex,
        currentSerial: existingSerials
      };
    } else if (current.currentLevel === 'item') {
      // Move to next item, inner case, case, or SSCC
      const nextItemIndex = current.itemIndex + 1 + itemsToSkip;
      
      if (configuration.useInnerCases) {
        const itemsPerInnerCase = configuration.itemsPerInnerCase;
        if (nextItemIndex < itemsPerInnerCase) {
          // More items in this inner case
          return {
            ...current,
            itemIndex: nextItemIndex
          };
        } else {
          // Move to next inner case
          const nextInnerCaseIndex = current.innerCaseIndex + 1;
          if (nextInnerCaseIndex < configuration.innerCasesPerCase) {
            return {
              ...current,
              innerCaseIndex: nextInnerCaseIndex,
              itemIndex: 0,
              currentLevel: 'innerCase'
            };
          } else {
            // Move to next case
            const nextCaseIndex = current.caseIndex + 1;
            if (nextCaseIndex < configuration.casesPerSscc) {
              return {
                ...current,
                caseIndex: nextCaseIndex,
                innerCaseIndex: 0,
                itemIndex: 0,
                currentLevel: 'case'
              };
            } else {
              // Move to next SSCC
              const nextSSCCIndex = current.ssccIndex + 1;
              if (nextSSCCIndex < configuration.numberOfSscc) {
                return {
                  ...current,
                  ssccIndex: nextSSCCIndex,
                  caseIndex: 0,
                  innerCaseIndex: 0,
                  itemIndex: 0,
                  currentLevel: 'sscc'
                };
              } else {
                // All done
                return {
                  ...current,
                  isComplete: true
                };
              }
            }
          }
        }
      } else if (configuration.casesPerSscc > 0) {
        // Cases → Items
        const itemsPerCase = configuration.itemsPerCase;
        if (nextItemIndex < itemsPerCase) {
          // More items in this case
          return {
            ...current,
            itemIndex: nextItemIndex
          };
        } else {
          // Move to next case
          const nextCaseIndex = current.caseIndex + 1;
          if (nextCaseIndex < configuration.casesPerSscc) {
            return {
              ...current,
              caseIndex: nextCaseIndex,
              itemIndex: 0,
              currentLevel: 'case'
            };
          } else {
            // Move to next SSCC
            const nextSSCCIndex = current.ssccIndex + 1;
            if (nextSSCCIndex < configuration.numberOfSscc) {
              return {
                ...current,
                ssccIndex: nextSSCCIndex,
                caseIndex: 0,
                itemIndex: 0,
                currentLevel: 'sscc'
              };
            } else {
              // All done
              return {
                ...current,
                isComplete: true
              };
            }
          }
        }
      } else {
        // Direct SSCC → Items
        const itemsPerSSCC = configuration.itemsPerCase;
        if (nextItemIndex < itemsPerSSCC) {
          // More items in this SSCC
          return {
            ...current,
            itemIndex: nextItemIndex
          };
        } else {
          // Move to next SSCC
          const nextSSCCIndex = current.ssccIndex + 1;
          if (nextSSCCIndex < configuration.numberOfSscc) {
            return {
              ...current,
              ssccIndex: nextSSCCIndex,
              itemIndex: 0,
              currentLevel: 'sscc'
            };
          } else {
            // All done
            return {
              ...current,
              isComplete: true
            };
          }
        }
      }
    }
    
    return current;
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
    // Get the package_ndc from the FDA response (10-digit format with dashes like "0574-0820-10")
    const packageNdc = productOption.packageNdc;
    const ndcParts = packageNdc.split('-');
    
    // STEP 1: Normalize to 11-digit NDC format for #packageNdc field
    // Left-pad each segment to 5-4-2 format and join with hyphens
    let normalizedPackageNdc = '';
    if (ndcParts.length >= 3) {
      const labelerPadded = ndcParts[0].padStart(5, '0');  // Pad to 5 digits
      const productPadded = ndcParts[1].padStart(4, '0');  // Pad to 4 digits  
      const packagePadded = ndcParts[2].padStart(2, '0');  // Pad to 2 digits
      normalizedPackageNdc = `${labelerPadded}-${productPadded}-${packagePadded}`;
    }
    
    // STEP 2: Process segments for #companyPrefix and #productCode
    let companyPrefix = '';
    let productCodeForGS1 = '';
    
    if (ndcParts.length >= 3) {
      // For #companyPrefix: Take first segment (without padding) and prepend "03"
      // Example: "0574" becomes "030574"
      companyPrefix = "03" + ndcParts[0];
      
      // For #productCode: Take last 2 segments (without padding) and concatenate without dash
      // Example: "0820" + "10" becomes "082010"  
      productCodeForGS1 = ndcParts[1] + ndcParts[2];
    } else {
      // Fallback for unexpected NDC format
      const rawPackageNdc = packageNdc.replace(/-/g, '');
      companyPrefix = "03" + rawPackageNdc.slice(0, 4);
      productCodeForGS1 = rawPackageNdc.slice(4);
    }
    
    // Store the normalized 11-digit NDC without hyphens for backend processing
    const packageNdcForStorage = normalizedPackageNdc.replace(/-/g, '');
    
    setConfiguration({
      ...configuration,
      productNdc: productOption.productNdc, // Store the original product NDC
      packageNdc: packageNdcForStorage, // Store the normalized 11-digit package NDC without hyphens
      companyPrefix: companyPrefix, // "03" + first segment (without padding)
      productCode: productCodeForGS1, // Last 2 segments concatenated (without padding)
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

  // ===== MULTI-PRODUCT HELPER FUNCTIONS =====
  
  // Get current active product
  const getCurrentProduct = () => {
    return products[activeProductIndex] || products[0];
  };
  
  // Update current product
  const updateCurrentProduct = (updates) => {
    const updatedProducts = [...products];
    updatedProducts[activeProductIndex] = {
      ...updatedProducts[activeProductIndex],
      ...updates
    };
    setProducts(updatedProducts);
  };
  
  // Add new product
  const addProduct = () => {
    const newProduct = {
      id: `product-${Date.now()}`,
      // Product Information (EPCClass)
      manufacturerName: '',
      regulatedProductName: '',
      packageNdc: '',
      productNdc: '',
      dosageFormType: '',
      strengthDescription: '',
      netContentDescription: '',
      companyPrefix: '',
      productCode: '',
      lotNumber: '',
      expirationDate: '',
      
      // Packaging Configuration (per product)
      itemsPerCase: '',
      casesPerSscc: '',
      numberOfSscc: 1,
      useInnerCases: false,
      innerCasesPerCase: '',
      itemsPerInnerCase: '',
      ssccExtensionDigit: '0',
      caseIndicatorDigit: '0',
      innerCaseIndicatorDigit: '0',
      itemIndicatorDigit: '0'
    };
    
    const updatedProducts = [...products, newProduct];
    setProducts(updatedProducts);
    setActiveProductIndex(updatedProducts.length - 1);
  };
  
  // Remove product
  const removeProduct = (index) => {
    if (products.length <= 1) return; // Don't allow removing the last product
    
    const updatedProducts = products.filter((_, i) => i !== index);
    setProducts(updatedProducts);
    
    // Adjust active index if needed
    if (activeProductIndex >= updatedProducts.length) {
      setActiveProductIndex(updatedProducts.length - 1);
    } else if (activeProductIndex > index) {
      setActiveProductIndex(activeProductIndex - 1);
    }
  };
  
  // Sync legacy configuration with current product (for backward compatibility)
  const syncLegacyConfiguration = () => {
    const currentProduct = getCurrentProduct();
    if (currentProduct) {
      setConfiguration({...currentProduct});
    }
  };

  // ===== FDA SEARCH FUNCTIONS =====
  
  // Search FDA for specific product
  const searchFDAForProduct = async (productIndex) => {
    const product = products[productIndex];
    if (!product.productNdc) {
      setError('Please enter a Product NDC to search');
      return;
    }

    setFdaModal({ ...fdaModal, isLoading: true });
    setError('');

    try {
      const response = await axios.get(
        `https://api.fda.gov/drug/ndc.json?search=product_ndc:"${product.productNdc}"&limit=1`,
        { timeout: 10000 }
      );

      if (response.data.results && response.data.results.length > 0) {
        const result = response.data.results[0];
        
        // Update the specific product
        const updatedProducts = [...products];
        updatedProducts[productIndex] = {
          ...updatedProducts[productIndex],
          manufacturerName: result.labeler_name || '',
          regulatedProductName: result.generic_name || result.brand_name || '',
          packageNdc: result.package_ndc || '',
          dosageFormType: result.dosage_form || '',
          strengthDescription: result.active_ingredients?.[0]?.strength || '',
          netContentDescription: result.packaging?.[0]?.description || ''
        };
        
        setProducts(updatedProducts);
        
        // Sync with legacy configuration if this is the active product
        if (productIndex === activeProductIndex) {
          setConfiguration({...updatedProducts[productIndex]});
        }
        
        setSuccess('FDA data populated successfully!');
      } else {
        setError('No FDA data found for this Product NDC');
      }
    } catch (error) {
      console.error('FDA API Error:', error);
      if (error.code === 'ECONNABORTED') {
        setError('FDA search timed out. Please try again.');
      } else {
        setError('Error searching FDA database. Please check the Product NDC and try again.');
      }
    } finally {
      setFdaModal({ ...fdaModal, isLoading: false });
    }
  };

  // ===== FDA SEARCH FUNCTIONS =====

  // ===== GS1 DATA MATRIX PARSING =====
  
  /**
   * Parse GS1 Data Matrix barcode to extract serial number
   * Example: 01003723360643092115000042751\x1D1729053110771565E
   * AI (01) = GTIN (14 digits), AI (21) = Serial Number (variable), etc.
   */
  const parseGS1DataMatrix = (scannedData) => {
    try {
      // Replace Group Separator character (ASCII 29) with pipe for visibility
      const cleanData = scannedData.replace(/\x1D/g, '|GS|');
      
      let parsedData = {
        gtin: null,
        serialNumber: null,
        lotNumber: null,
        expirationDate: null,
        rawData: scannedData,
        cleanData
      };
      
      // Parse step by step through the GS1 data
      let position = 0;
      let dataString = scannedData;
      
      // Extract GTIN (AI 01) - always 14 digits
      if (dataString.startsWith('01')) {
        parsedData.gtin = dataString.substring(2, 16); 
        position = 16;
      }
      
      // Extract Serial Number (AI 21) - variable length until next AI or GS
      if (dataString.substring(position, position + 2) === '21') {
        position += 2; // skip AI
        let endPos = dataString.indexOf('\x1D', position); // find next group separator
        if (endPos === -1) {
          // Look for next AI pattern if no GS found
          const nextAI = dataString.substring(position).match(/(\d{2})/g);
          if (nextAI && nextAI.length > 1) {
            // Find position of second AI pattern
            endPos = position + dataString.substring(position).search(/\d{2}(?=\d)/);
          } else {
            endPos = dataString.length; // use rest of string
          }
        }
        parsedData.serialNumber = dataString.substring(position, endPos);
        position = endPos;
      }
      
      // Skip Group Separator if present
      if (dataString.charAt(position) === '\x1D') {
        position++;
      }
      
      // Extract Expiration Date (AI 17) - 6 digits YYMMDD
      if (dataString.substring(position, position + 2) === '17') {
        parsedData.expirationDate = dataString.substring(position + 2, position + 8);
        position += 8;
      }
      
      // Extract Lot/Batch Number (AI 10) - variable length
      if (dataString.substring(position, position + 2) === '10') {
        position += 2; // skip AI
        parsedData.lotNumber = dataString.substring(position); // rest of string
      }
      
      return parsedData;
      
    } catch (error) {
      console.error('❌ Error parsing GS1 Data Matrix:', error);
      return {
        gtin: null,
        serialNumber: scannedData, // Fallback to raw data
        lotNumber: null,
        expirationDate: null,
        rawData: scannedData,
        cleanData: scannedData
      };
    }
  };

  // ===== SCANDIT SCANNER FUNCTIONS =====

  /**
   * Initialize ScandIt scanner instance
   */
  const initializeScandItScanner = async () => {
    try {
      if (!scandItScannerRef.current) {
        scandItScannerRef.current = new SimpleScandItScanner(SCANDIT_LICENSE_KEY);
      }
      return scandItScannerRef.current;
    } catch (error) {
      console.error('❌ Failed to initialize ScandIt scanner:', error);
      throw error;
    }
  };

  /**
   * Handle successful barcode scan from ScandIt
   */
  const handleScandItScan = (scannedData, scanMode) => {
    console.log(`📱 ScandIt ${scanMode} scan:`, scannedData);

    // Validate that this is a GS1 Data Matrix barcode (maintain existing validation)
    const validation = validateGS1Barcode(scannedData);
    
    if (!validation.isValid) {
      setError(`❌ Invalid barcode type. Only 2D Data Matrix codes with GS1 data are supported. ${validation.reason}`);
      return;
    }

    // Clear any previous errors and process the scan
    setError('');
    console.log('✅ Valid GS1 Data Matrix code detected:', validation.reason);
    
    // Use existing barcode result processing logic
    handleBarcodeResult(scannedData);
  };

  /**
   * Start ScandIt scanning based on scanning context
   */
  const startScandItScanning = async () => {
    try {
      setIsScanning(true);
      setError('');

      if (!scannerContainerRef.current) {
        throw new Error('Scanner container not available');
      }

      const scanner = await initializeScandItScanner();
      
      // Initialize scanner with GS1 parsing callback
      await scanner.createScanner(scannerContainerRef.current, (scannedData) => {
        // Parse GS1 Data Matrix to extract serial number
        const parsedData = parseGS1DataMatrix(scannedData);
        
        if (parsedData.serialNumber) {
          handleScandItScan(parsedData.serialNumber, 'single');
        } else {
          handleScandItScan(scannedData, 'single');
        }
      });

      await scanner.startScanning();

    } catch (error) {
      console.error('❌ Failed to start working ScandIt scanner:', error);
      setIsScanning(false);
      
      if (error.message.includes('permission')) {
        setError('Camera access denied. Please allow camera permissions and try again.');
      } else if (error.message.includes('camera')) {
        setError('No camera found on this device.');
      } else {
        setError(`Failed to start scanner: ${error.message}`);
      }
    }
  };

  /**
   * Start continuous ScandIt scanning (batch mode)
   */
  const startScandItContinuousScanning = async () => {
    // For ScandIt, continuous scanning is the same as regular scanning
    // The mode is determined by the scanning context
    await startScandItScanning();
  };

  // Legacy scanner functions (for existing ZXing-based scanning)
  const startScanLoop = async () => {
    // This function is called by existing scanner code
    // For now, redirect to ScandIt scanning
    await startScandItScanning();
  };

  // Barcode scanning functions
  const openScanner = (targetField, targetSetter) => {
    // Determine if this is multi-item scanning for Items level
    const isItemsLevel = serialCollectionStep.currentLevel === 'item';
    const itemCount = isItemsLevel ? getCurrentItemCount() : 1;
    
    setScannedItems([]);
    setRequiredItemCount(itemCount);
    setShouldContinueScanning(isItemsLevel && itemCount > 1);
    setScannerModal({ isOpen: true, targetField, targetSetter });
  };

  const removeScannedItem = (indexToRemove) => {
    setScannedItems(prevItems => {
      const newItems = prevItems.filter((_, index) => index !== indexToRemove);
      
      // Update success message to reflect new count
      if (newItems.length > 0) {
        setSuccess(`${newItems.length} of ${requiredItemCount} items scanned`);
      } else {
        setSuccess('');
      }
      
      return newItems;
    });
  };

  /**
   * Stop scanning and cleanup
   */
  const closeScanner = async () => {
    try {
      console.log('🛑 Closing ScandIt scanner...');
      
      setIsScanning(false);
      setScannerModal({ isOpen: false, targetField: '', targetSetter: null });
      
      if (scandItScannerRef.current) {
        await scandItScannerRef.current.stopScanning();
        // Note: We don't dispose the scanner instance to avoid re-initialization costs
        // It will be reused for subsequent scans
      }
      
      // Clear multi-scanning state
      setScannedItems([]);
      setRequiredItemCount(1);
      setShouldContinueScanning(false);
      
      // Clear any scanner-related errors
      if (error && error.includes('scanner')) {
        setError('');
      }
      
      console.log('✅ ScandIt scanner closed');
      
    } catch (error) {
      console.error('❌ Error closing scanner:', error);
      // Don't show error to user for cleanup issues
    }
  };

  // Cleanup ScandIt resources on component unmount
  useEffect(() => {
    return () => {
      if (scandItScannerRef.current) {
        scandItScannerRef.current.dispose().catch(console.error);
      }
    };
  }, []);

  const validateGS1Barcode = (scannedData) => {
    // GS1 barcodes contain FNC1 characters (ASCII 29 / Group Separator)
    const GS1_SEPARATOR = '\u001d';
    
    // Check for GS1 FNC1 character
    if (scannedData.includes(GS1_SEPARATOR)) {
      return { isValid: true, reason: 'Contains GS1 FNC1 separator' };
    }
    
    // Check for common GS1 Application Identifier patterns
    // AI 01 (GTIN), AI 21 (Serial), AI 17 (Expiry), AI 10 (Lot), AI 00 (SSCC)
    const gs1Patterns = [
      /^01\d{14}/,  // AI 01 + 14-digit GTIN
      /^00\d{18}/,  // AI 00 + 18-digit SSCC
      /\b01\d{14}/,  // AI 01 anywhere in string
      /\b21[\w\d]+/, // AI 21 (Serial number)
      /\b17\d{6}/,   // AI 17 + 6-digit date (YYMMDD)
      /\b10[\w\d]+/, // AI 10 (Batch/Lot)
      /\b11\d{6}/    // AI 11 + 6-digit date (YYMMDD)
    ];
    
    // Check if data matches any GS1 AI patterns
    for (const pattern of gs1Patterns) {
      if (pattern.test(scannedData)) {
        return { isValid: true, reason: `Matches GS1 pattern: ${pattern}` };
      }
    }
    
    // Check if it's a simple alphanumeric code that could be a serial number
    // Allow if it's reasonable length and contains letters/numbers
    if (scannedData.length >= 4 && scannedData.length <= 50 && /^[A-Za-z0-9\-_]+$/.test(scannedData)) {
      return { isValid: true, reason: 'Valid alphanumeric serial number format' };
    }
    
    return { 
      isValid: false, 
      reason: 'Does not contain GS1 FNC1 characters or valid GS1 Application Identifiers. This appears to be a consumer product barcode (UPC/EAN).' 
    };
  };

  const handleBarcodeResult = (scannedData) => {
    try {
      // First validate that this is a GS1 barcode
      const validation = validateGS1Barcode(scannedData);
      
      if (!validation.isValid) {
        setError(`❌ Non-GS1 barcode detected. ${validation.reason}`);
        return; // Don't close scanner, let it continue
      }
      
      // Parse GS1 Data Matrix barcode
      const parsedData = parseGS1Barcode(scannedData);
      
      console.log('Parsed GS1 Data:', parsedData); // Debug log
      
      if (parsedData.serialNumber) {
        const serialNumber = parsedData.serialNumber;
        const isItemsLevel = serialCollectionStep.currentLevel === 'item';
        
        // Check for duplicates against ALL existing serial numbers in the project
        const currentPath = getCurrentPath();
        console.log('Checking duplicates for:', serialNumber, 'currentPath:', currentPath);
        const duplicates = validateDuplicateSerials(serialNumber, currentPath);
        console.log('Duplicate check result:', duplicates);
        
        if (duplicates) {
          console.log('DUPLICATE FOUND - should show error');
          setError(`🚫 DUPLICATE DETECTED! "${serialNumber}" is already used at: ${duplicates[0].path}`);
          // Show error for longer time for duplicates
          setTimeout(() => {
            if (scannerModal.isOpen && isScanning) {
              // Continue scanning after showing duplicate error
              console.log('Continuing scan after duplicate error');
            }
          }, 2000);
          return;
        } else {
          console.log('No duplicates found - proceeding with scan');
        }
        
        // Clear any previous errors
        setError('');
        
        // SUCCESS: Provide haptic feedback and audio beep for successful scan
        try {
          // Haptic feedback - multiple methods for iOS compatibility
          if (window.navigator && window.navigator.vibrate) {
            window.navigator.vibrate([200]); // Array format for iOS
            window.navigator.vibrate(200);   // Standard format
          }
          
          if (navigator.vibrate && typeof navigator.vibrate === 'function') {
            navigator.vibrate(200);
          }
          
          // Audio beep
          const audio = new Audio();
          audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmYfCC+N0fHSgS0FK3zD7uGWRgoXY7zs3ZdQEwxOqeXtrGcdCFOx3/PsmTIBJHzE7uiT';
          audio.volume = 0.3;
          audio.play().catch(() => {
            // Fallback to Web Audio API if simple audio fails
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.3);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
          });
          
        } catch (feedbackError) {
          // Silently handle feedback errors to avoid disrupting scan workflow
          console.log('Scan feedback unavailable:', feedbackError.message);
        }
        
        // Handle different scanner target fields
        if (scannerModal.targetField === 'edit') {
          // Set the scanned serial number in edit modal
          setEditModal({
            ...editModal,
            currentValue: serialNumber
          });
          
          // Show success message
          setSuccess(`Scanned serial number: ${serialNumber}`);
          closeScanner();
        } else if (isItemsLevel && requiredItemCount > 1) {
          // Multi-scanning for Items level - use functional update to ensure we have the latest state
          setScannedItems(prevScannedItems => {
            // Check if this serial number is already in the scanned items
            if (prevScannedItems.includes(serialNumber)) {
              setError(`🚫 DUPLICATE IN SESSION! "${serialNumber}" was already scanned in this session.`);
              return prevScannedItems; // Return unchanged
            }
            
            const newScannedItems = [...prevScannedItems, serialNumber];
            
            // Show progress message
            setSuccess(`Scanned ${newScannedItems.length} of ${requiredItemCount} items: ${serialNumber}`);
            
            if (newScannedItems.length >= requiredItemCount) {
              // All items scanned, update the textarea and close scanner
              const itemsText = newScannedItems.join('\n');
              setSerialCollectionStep({
                ...serialCollectionStep,
                currentSerial: itemsText
              });
              
              // Show completion message
              setSuccess(`All ${requiredItemCount} items scanned successfully!`);
              setShouldContinueScanning(false);
              setTimeout(() => closeScanner(), 500); // Small delay to show completion message
            }
            
            return newScannedItems;
          });
          
          // Note: Don't close scanner here - let it continue scanning for more items
        } else {
          // Single item scanning (SSCC, Case, Inner Case, or single Item)
          setSerialCollectionStep({
            ...serialCollectionStep,
            currentSerial: serialNumber
          });
          
          // Show detailed success message
          let successMessage = `Scanned serial number: ${serialNumber}`;
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
          // For single item scanning, close the scanner
          setTimeout(() => closeScanner(), 100);
        }
      } else {
        setError('Could not extract serial number from barcode');
      }
      
    } catch (error) {
      console.error('Error parsing barcode:', error);
      setError('Error parsing barcode data');
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

  // Scanner modal useEffect for ScandIt integration
  useEffect(() => {
    if (scannerModal.isOpen) {
      // Small delay to ensure modal and ScandIt container are rendered
      setTimeout(() => {
        startScandItScanning(); // Use new ScandIt scanner
      }, 200);
    } else {
      // Stop ScandIt scanner when modal closes
      console.log('Scanner modal closed - stopping ScandIt scanner');
      closeScanner();
    }
  }, [scannerModal.isOpen]);

  // Scroll to top when step changes
  useEffect(() => {
    if (currentStep > 1) {
      scrollToTop();
    }
  }, [currentStep]);

  const calculateTotals = () => {
    // Parse values to ensure they are numbers
    const numberOfSscc = parseInt(configuration.numberOfSscc) || 0;
    const casesPerSscc = parseInt(configuration.casesPerSscc) || 0;
    const itemsPerCase = parseInt(configuration.itemsPerCase) || 0;
    const useInnerCases = configuration.useInnerCases;
    const innerCasesPerCase = parseInt(configuration.innerCasesPerCase) || 0;
    const itemsPerInnerCase = parseInt(configuration.itemsPerInnerCase) || 0;
    
    // Debug logging
    console.log('calculateTotals - Configuration values:', {
      numberOfSscc,
      casesPerSscc,
      itemsPerCase,
      useInnerCases,
      innerCasesPerCase,
      itemsPerInnerCase
    });
    
    // If no cases, items go directly in SSCC
    if (casesPerSscc === 0) {
      const totalItems = itemsPerCase * numberOfSscc;
      console.log('calculateTotals - Direct SSCC->Items:', { totalItems });
      return { totalCases: 0, totalInnerCases: 0, totalItems };
    }
    
    const totalCases = casesPerSscc * numberOfSscc;
    if (useInnerCases) {
      const totalInnerCases = innerCasesPerCase * totalCases;
      const totalItems = itemsPerInnerCase * totalInnerCases;
      console.log('calculateTotals - With Inner Cases:', { totalCases, totalInnerCases, totalItems });
      return { totalCases, totalInnerCases, totalItems };
    } else {
      const totalItems = itemsPerCase * totalCases;
      console.log('calculateTotals - Without Inner Cases:', { totalCases, totalItems });
      return { totalCases, totalInnerCases: 0, totalItems };
    }
  };

  // Calculate totals based on current product
  const calculateCurrentProductTotals = () => {
    const product = getCurrentProduct();
    const numberOfSscc = parseInt(product.numberOfSscc) || 0;
    const casesPerSscc = parseInt(product.casesPerSscc) || 0;
    const itemsPerCase = parseInt(product.itemsPerCase) || 0;
    const useInnerCases = product.useInnerCases;
    const innerCasesPerCase = parseInt(product.innerCasesPerCase) || 0;
    const itemsPerInnerCase = parseInt(product.itemsPerInnerCase) || 0;
    
    // If no cases, items go directly in SSCC
    if (casesPerSscc === 0) {
      const totalItems = itemsPerCase * numberOfSscc;
      return { totalCases: 0, totalInnerCases: 0, totalItems };
    }
    
    const totalCases = casesPerSscc * numberOfSscc;
    if (useInnerCases) {
      const totalInnerCases = innerCasesPerCase * totalCases;
      const totalItems = itemsPerInnerCase * totalInnerCases;
      return { totalCases, totalInnerCases, totalItems };
    } else {
      const totalItems = itemsPerCase * totalCases;
      return { totalCases, totalInnerCases: 0, totalItems };
    }
  };

  const renderStep1 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit}>
        
        <div className="business-document-section">
          <h3>Business Document Information</h3>
          <div className="business-entities-grid">
            
            {/* Sender Information */}
            <div className="business-entity-group">
              <div className="flex justify-between items-center mb-4">
                <h4>Sender Information</h4>
                <button
                  type="button"
                  onClick={() => openLocationSelector('sender')}
                  className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Select a saved location to fill in sender information"
                >
                  Select Location
                </button>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="senderCompanyPrefix">GS1 Company Prefix:</label>
                  <input
                    type="text"
                    id="senderCompanyPrefix"
                    value={configuration.senderCompanyPrefix}
                    onChange={(e) => setConfiguration({...configuration, senderCompanyPrefix: e.target.value})}
                    placeholder="e.g., 0367891"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderGln">GLN (Global Location Number):</label>
                  <input
                    type="text"
                    id="senderGln"
                    value={configuration.senderGln}
                    onChange={(e) => setConfiguration({...configuration, senderGln: e.target.value})}
                    placeholder="e.g., 0367891000015"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderSgln">SGLN (Serialized GLN):</label>
                  <input
                    type="text"
                    id="senderSgln"
                    value={configuration.senderSgln}
                    onChange={(e) => setConfiguration({...configuration, senderSgln: e.target.value})}
                    placeholder="e.g., 0367891.00001.0"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderName">Company Name:</label>
                  <input
                    type="text"
                    id="senderName"
                    value={configuration.senderName}
                    onChange={(e) => setConfiguration({...configuration, senderName: e.target.value})}
                    placeholder="e.g., Pharma US LLC"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderStreetAddress">Street Address:</label>
                  <input
                    type="text"
                    id="senderStreetAddress"
                    value={configuration.senderStreetAddress}
                    onChange={(e) => setConfiguration({...configuration, senderStreetAddress: e.target.value})}
                    placeholder="e.g., 1255 Main St"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderCity">City:</label>
                  <input
                    type="text"
                    id="senderCity"
                    value={configuration.senderCity}
                    onChange={(e) => setConfiguration({...configuration, senderCity: e.target.value})}
                    placeholder="e.g., Salt Lake City"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderState">State:</label>
                  <input
                    type="text"
                    id="senderState"
                    value={configuration.senderState}
                    onChange={(e) => setConfiguration({...configuration, senderState: e.target.value})}
                    placeholder="e.g., UT"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderPostalCode">Postal Code:</label>
                  <input
                    type="text"
                    id="senderPostalCode"
                    value={configuration.senderPostalCode}
                    onChange={(e) => setConfiguration({...configuration, senderPostalCode: e.target.value})}
                    placeholder="e.g., 84044"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderCountryCode">Country Code:</label>
                  <input
                    type="text"
                    id="senderCountryCode"
                    value={configuration.senderCountryCode}
                    onChange={(e) => setConfiguration({...configuration, senderCountryCode: e.target.value})}
                    placeholder="e.g., US"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="senderDespatchAdviceNumber">Despatch Advice Number:</label>
                  <input
                    type="text"
                    id="senderDespatchAdviceNumber"
                    value={configuration.senderDespatchAdviceNumber}
                    onChange={(e) => setConfiguration({...configuration, senderDespatchAdviceNumber: e.target.value})}
                    placeholder="e.g., 202500221"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Receiver Information */}
            <div className="business-entity-group">
              <div className="flex justify-between items-center mb-4">
                <h4>Receiver Information</h4>
                <button
                  type="button"
                  onClick={() => openLocationSelector('receiver')}
                  className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Select a saved location to fill in receiver information"
                >
                  Select Location
                </button>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="receiverCompanyPrefix">GS1 Company Prefix (optional):</label>
                  <input
                    type="text"
                    id="receiverCompanyPrefix"
                    value={configuration.receiverCompanyPrefix}
                    onChange={(e) => setConfiguration({...configuration, receiverCompanyPrefix: e.target.value})}
                    placeholder="e.g., 0345802"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverGln">GLN (Global Location Number):</label>
                  <input
                    type="text"
                    id="receiverGln"
                    value={configuration.receiverGln}
                    onChange={(e) => setConfiguration({...configuration, receiverGln: e.target.value})}
                    placeholder="e.g., 0345802000021"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverSgln">SGLN (Serialized GLN):</label>
                  <input
                    type="text"
                    id="receiverSgln"
                    value={configuration.receiverSgln}
                    onChange={(e) => setConfiguration({...configuration, receiverSgln: e.target.value})}
                    placeholder="e.g., 1034580200021..0"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverName">Company Name:</label>
                  <input
                    type="text"
                    id="receiverName"
                    value={configuration.receiverName}
                    onChange={(e) => setConfiguration({...configuration, receiverName: e.target.value})}
                    placeholder="e.g., Pharmacy Corp"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverStreetAddress">Street Address:</label>
                  <input
                    type="text"
                    id="receiverStreetAddress"
                    value={configuration.receiverStreetAddress}
                    onChange={(e) => setConfiguration({...configuration, receiverStreetAddress: e.target.value})}
                    placeholder="e.g., 123 Main St"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverCity">City:</label>
                  <input
                    type="text"
                    id="receiverCity"
                    value={configuration.receiverCity}
                    onChange={(e) => setConfiguration({...configuration, receiverCity: e.target.value})}
                    placeholder="e.g., New York"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverState">State:</label>
                  <input
                    type="text"
                    id="receiverState"
                    value={configuration.receiverState}
                    onChange={(e) => setConfiguration({...configuration, receiverState: e.target.value})}
                    placeholder="e.g., NY"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverPostalCode">Postal Code:</label>
                  <input
                    type="text"
                    id="receiverPostalCode"
                    value={configuration.receiverPostalCode}
                    onChange={(e) => setConfiguration({...configuration, receiverPostalCode: e.target.value})}
                    placeholder="e.g., 10001"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverCountryCode">Country Code:</label>
                  <input
                    type="text"
                    id="receiverCountryCode"
                    value={configuration.receiverCountryCode}
                    onChange={(e) => setConfiguration({...configuration, receiverCountryCode: e.target.value})}
                    placeholder="e.g., US"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="receiverPoNumber">PO Number:</label>
                  <input
                    type="text"
                    id="receiverPoNumber"
                    value={configuration.receiverPoNumber}
                    onChange={(e) => setConfiguration({...configuration, receiverPoNumber: e.target.value})}
                    placeholder="e.g., 1002345"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Shipper Information */}
            <div className="business-entity-group">
              <div className="flex justify-between items-center mb-4">
                <h4>Shipper Information</h4>
                <button
                  type="button"
                  onClick={() => openLocationSelector('shipper')}
                  className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  title="Select a saved location to fill in shipper information"
                >
                  Select Location
                </button>
              </div>
              <div className="form-group shipper-same-checkbox">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={configuration.shipperSameAsSender}
                    onChange={(e) => {
                      const isSame = e.target.checked;
                      setConfiguration({
                        ...configuration,
                        shipperSameAsSender: isSame,
                        shipperCompanyPrefix: isSame ? configuration.senderCompanyPrefix : configuration.shipperCompanyPrefix,
                        shipperGln: isSame ? configuration.senderGln : configuration.shipperGln,
                        shipperSgln: isSame ? configuration.senderSgln : configuration.shipperSgln,
                        shipperName: isSame ? configuration.senderName : configuration.shipperName,
                        shipperStreetAddress: isSame ? configuration.senderStreetAddress : configuration.shipperStreetAddress,
                        shipperCity: isSame ? configuration.senderCity : configuration.shipperCity,
                        shipperState: isSame ? configuration.senderState : configuration.shipperState,
                        shipperPostalCode: isSame ? configuration.senderPostalCode : configuration.shipperPostalCode,
                        shipperCountryCode: isSame ? configuration.senderCountryCode : configuration.shipperCountryCode
                      });
                    }}
                  />
                  <span className="checkbox-custom"></span>
                  Shipper is same as Sender
                </label>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="shipperCompanyPrefix">GS1 Company Prefix:</label>
                  <input
                    type="text"
                    id="shipperCompanyPrefix"
                    value={configuration.shipperCompanyPrefix}
                    onChange={(e) => setConfiguration({...configuration, shipperCompanyPrefix: e.target.value})}
                    placeholder="e.g., 0345802"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperGln">GLN (Global Location Number):</label>
                  <input
                    type="text"
                    id="shipperGln"
                    value={configuration.shipperGln}
                    onChange={(e) => setConfiguration({...configuration, shipperGln: e.target.value})}
                    placeholder="e.g., 0345802000014"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperSgln">SGLN (Serialized GLN):</label>
                  <input
                    type="text"
                    id="shipperSgln"
                    value={configuration.shipperSgln}
                    onChange={(e) => setConfiguration({...configuration, shipperSgln: e.target.value})}
                    placeholder="e.g., 0345802.0000.0"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperName">Company Name:</label>
                  <input
                    type="text"
                    id="shipperName"
                    value={configuration.shipperName}
                    onChange={(e) => setConfiguration({...configuration, shipperName: e.target.value})}
                    placeholder="e.g., Shipping Corp"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperStreetAddress">Street Address:</label>
                  <input
                    type="text"
                    id="shipperStreetAddress"
                    value={configuration.shipperStreetAddress}
                    onChange={(e) => setConfiguration({...configuration, shipperStreetAddress: e.target.value})}
                    placeholder="e.g., 456 Shipping Ave"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperCity">City:</label>
                  <input
                    type="text"
                    id="shipperCity"
                    value={configuration.shipperCity}
                    onChange={(e) => setConfiguration({...configuration, shipperCity: e.target.value})}
                    placeholder="e.g., Chicago"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperState">State:</label>
                  <input
                    type="text"
                    id="shipperState"
                    value={configuration.shipperState}
                    onChange={(e) => setConfiguration({...configuration, shipperState: e.target.value})}
                    placeholder="e.g., IL"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperPostalCode">Postal Code:</label>
                  <input
                    type="text"
                    id="shipperPostalCode"
                    value={configuration.shipperPostalCode}
                    onChange={(e) => setConfiguration({...configuration, shipperPostalCode: e.target.value})}
                    placeholder="e.g., 60007"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="shipperCountryCode">Country Code:</label>
                  <input
                    type="text"
                    id="shipperCountryCode"
                    value={configuration.shipperCountryCode}
                    onChange={(e) => setConfiguration({...configuration, shipperCountryCode: e.target.value})}
                    placeholder="e.g., US"
                    disabled={configuration.shipperSameAsSender}
                    required
                  />
                </div>
              </div>
            </div>

          </div>
        </div>
        
        <div className="epcclass-section">
          <div className="flex justify-between items-center mb-4">
            <h3>Product Information (EPCClass)</h3>
            <button
              type="button"
              onClick={addProduct}
              className="btn-secondary"
            >
              + Add Product
            </button>
          </div>
          
          {/* Product Tabs */}
          {products.length > 1 && (
            <div className="product-tabs">
              {products.map((product, index) => (
                <button
                  key={product.id}
                  type="button"
                  onClick={() => setActiveProductIndex(index)}
                  className={`product-tab ${index === activeProductIndex ? 'active' : ''}`}
                >
                  Product {index + 1}
                  {product.productNdc && ` (NDC: ${product.productNdc})`}
                  {products.length > 1 && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeProduct(index);
                      }}
                      className="remove-product-btn"
                    >
                      ×
                    </button>
                  )}
                </button>
              ))}
            </div>
          )}
          
          {/* Current Product Form */}
          <div className="current-product-form">
            <div className="form-grid search-fda-wrapper">
              <div className="form-group fda-search-group">
                <label htmlFor="productNdc">Search FDA by Product NDC:</label>
                <div className="fda-search-container">
                  <input
                    type="text"
                    id="productNdc"
                    value={getCurrentProduct().productNdc || ''}
                    onChange={(e) => updateCurrentProduct({productNdc: e.target.value})}
                    placeholder="Enter Product NDC (format: 12345-678-90)"
                    className="fda-search-input"
                  />
                  <button
                    type="button"
                    onClick={() => searchFDAForProduct(activeProductIndex)}
                    disabled={fdaModal.isLoading}
                    className="fda-search-button"
                  >
                    {fdaModal.isLoading ? 'Searching...' : 'Search FDA'}
                  </button>
                </div>
              </div>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="companyPrefix">GS1 Company Prefix:</label>
                <input
                  type="text"
                  id="companyPrefix"
                  value={getCurrentProduct().companyPrefix || ''}
                  onChange={(e) => updateCurrentProduct({companyPrefix: e.target.value})}
                  placeholder="e.g., 0345802"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="productCode">Product Code:</label>
                <input
                  type="text"
                  id="productCode"
                  value={getCurrentProduct().productCode || ''}
                  onChange={(e) => updateCurrentProduct({productCode: e.target.value})}
                  placeholder="e.g., 46611"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="manufacturerName">Manufacturer Name:</label>
                <input
                  type="text"
                  id="manufacturerName"
                  value={getCurrentProduct().manufacturerName || ''}
                  onChange={(e) => updateCurrentProduct({manufacturerName: e.target.value})}
                  placeholder="e.g., Padagis Israel Pharmaceuticals Ltd"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="regulatedProductName">Regulated Product Name:</label>
                <input
                  type="text"
                  id="regulatedProductName"
                  value={getCurrentProduct().regulatedProductName || ''}
                  onChange={(e) => updateCurrentProduct({regulatedProductName: e.target.value})}
                  placeholder="e.g., Econazole Nitrate"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="packageNdc">Package NDC:</label>
                <input
                  type="text"
                  id="packageNdc"
                  value={getCurrentProduct().packageNdc || ''}
                  onChange={(e) => updateCurrentProduct({packageNdc: e.target.value})}
                  placeholder="e.g., 45802046611"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="dosageFormType">Dosage Form Type:</label>
                <input
                  type="text"
                  id="dosageFormType"
                  value={getCurrentProduct().dosageFormType || ''}
                  onChange={(e) => updateCurrentProduct({dosageFormType: e.target.value})}
                  placeholder="e.g., CREAM"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="strengthDescription">Strength Description:</label>
                <input
                  type="text"
                  id="strengthDescription"
                  value={getCurrentProduct().strengthDescription || ''}
                  onChange={(e) => updateCurrentProduct({strengthDescription: e.target.value})}
                  placeholder="e.g., ECONAZOLE NITRATE 10 mg/g"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="netContentDescription">Net Content Description:</label>
                <input
                  type="text"
                  id="netContentDescription"
                  value={getCurrentProduct().netContentDescription || ''}
                  onChange={(e) => updateCurrentProduct({netContentDescription: e.target.value})}
                  placeholder="e.g., 1 TUBE in 1 CARTON (45802-466-11) / 30 g in 1 TUBE"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="lotNumber">Lot Number:</label>
                <input
                  type="text"
                  id="lotNumber"
                  value={getCurrentProduct().lotNumber || ''}
                  onChange={(e) => updateCurrentProduct({lotNumber: e.target.value})}
                  placeholder="e.g., LOT123"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="expirationDate">Expiration Date:</label>
                <input
                  type="date"
                  id="expirationDate"
                  value={getCurrentProduct().expirationDate || ''}
                  onChange={(e) => updateCurrentProduct({expirationDate: e.target.value})}
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <div className="inner-case-section">
          <h3>Packaging Configuration (Product {activeProductIndex + 1}) {isPackagingConfigLocked && <span className="locked-indicator">(Locked - Serial Numbers Entered)</span>}</h3>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="numberOfSscc">Number of SSCCs:</label>
              <input
                type="tel"
                id="numberOfSscc"
                inputMode="numeric"
                pattern="[0-9]*"
                min="1"
                max="20"
                value={getCurrentProduct().numberOfSscc}
                onChange={(e) => {
                  const value = e.target.value;
                  const parsedValue = value === '' ? '' : parseInt(value);
                  updateCurrentProduct({
                    numberOfSscc: isNaN(parsedValue) ? '' : parsedValue
                  });
                }}
                disabled={isPackagingConfigLocked}
                placeholder="e.g., 1"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="casesPerSscc">Cases per SSCC:</label>
              <input
                type="tel"
                id="casesPerSscc"
                inputMode="numeric"
                pattern="[0-9]*"
                min="0"
                max="500000"
                value={getCurrentProduct().casesPerSscc}
                onChange={(e) => {
                  const value = e.target.value;
                  const parsedValue = value === '' ? '' : parseInt(value);
                  updateCurrentProduct({casesPerSscc: isNaN(parsedValue) ? '' : parsedValue});
                }}
                disabled={isPackagingConfigLocked}
                placeholder="e.g., 5 (or 0 for direct SSCC → Items)"
                required
              />
              <small className="form-hint">Enter 0 for direct SSCC → Items aggregation</small>
            </div>
          </div>
          
          <div className="packaging-option">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={getCurrentProduct().useInnerCases}
                onChange={(e) => updateCurrentProduct({useInnerCases: e.target.checked})}
                disabled={getCurrentProduct().casesPerSscc === 0 || getCurrentProduct().casesPerSscc === '' || isPackagingConfigLocked}
              />
              <span className="checkbox-text">
                <strong>Enable Inner Cases</strong>
                <small>{(getCurrentProduct().casesPerSscc === 0 || getCurrentProduct().casesPerSscc === '') ? 'Not available when Cases per SSCC = 0 or empty' : 'Add an intermediate packaging level between cases and items'}</small>
              </span>
            </label>
          </div>
          
          {getCurrentProduct().casesPerSscc === 0 ? (
            <div className="packaging-config">
              <div className="form-group">
                <label htmlFor="itemsPerCase">Items per SSCC:</label>
                <input
                  type="tel"
                  id="itemsPerCase"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  min="1"
                  max="100000000"
                  value={getCurrentProduct().itemsPerCase}
                  onChange={(e) => {
                    const value = e.target.value;
                    const parsedValue = value === '' ? '' : parseInt(value);
                    updateCurrentProduct({itemsPerCase: isNaN(parsedValue) ? '' : parsedValue});
                  }}
                  disabled={isPackagingConfigLocked}
                  placeholder="e.g., 10"
                  required
                />
              </div>
              <div className="config-explanation">
                <p><strong>2-Level Hierarchy:</strong> SSCC → Items</p>
              </div>
            </div>
          ) : getCurrentProduct().useInnerCases ? (
            <div className="packaging-config">
              <div className="grid grid-cols-2 gap-4 mb-0">
                <div className="form-group">
                  <label htmlFor="innerCasesPerCase">Inner Cases per Case:</label>
                  <input
                    type="tel"
                    id="innerCasesPerCase"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    min="1"
                    max="50000"
                    value={getCurrentProduct().innerCasesPerCase}
                    onChange={(e) => {
                      const value = e.target.value;
                      const parsedValue = value === '' ? '' : parseInt(value);
                      updateCurrentProduct({innerCasesPerCase: isNaN(parsedValue) ? '' : parsedValue});
                    }}
                    disabled={isPackagingConfigLocked}
                    placeholder="e.g., 2"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="itemsPerInnerCase">Items per Inner Case:</label>
                  <input
                    type="tel"
                    id="itemsPerInnerCase"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    min="1"
                    max="100000"
                    value={getCurrentProduct().itemsPerInnerCase}
                    onChange={(e) => {
                      const value = e.target.value;
                      const parsedValue = value === '' ? '' : parseInt(value);
                      updateCurrentProduct({itemsPerInnerCase: isNaN(parsedValue) ? '' : parsedValue});
                    }}
                    disabled={isPackagingConfigLocked}
                    placeholder="e.g., 5"
                    required
                  />
                </div>
              </div>
              <div className="config-explanation">
                <p><strong>4-Level Hierarchy:</strong> SSCC → Cases → Inner Cases → Items</p>
              </div>
            </div>
          ) : (
            <div className="packaging-config">
              
              <div className="form-group">
                <label htmlFor="itemsPerCase">Items per Case:</label>
                <input
                  type="number"
                  id="itemsPerCase"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  min="1"
                  max="100"
                  value={getCurrentProduct().itemsPerCase}
                  onChange={(e) => {
                    const value = e.target.value;
                    const parsedValue = value === '' ? '' : parseInt(value);
                    updateCurrentProduct({itemsPerCase: isNaN(parsedValue) ? '' : parsedValue});
                  }}
                  disabled={isPackagingConfigLocked}
                  placeholder="e.g., 10"
                  required
                />
              </div>
              <div className="config-explanation">
                <p><strong>3-Level Hierarchy:</strong> SSCC → Cases → Items</p>
              </div>
            </div>
          )}
          
          <div className="gs1-indicators">
            <h4>GS1 Indicator/Extension Digits</h4>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="ssccExtensionDigit">SSCC Extension Digit:</label>
                <input
                  type="tel"
                  id="ssccExtensionDigit"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength="1"
                  value={getCurrentProduct().ssccExtensionDigit}
                  onChange={(e) => updateCurrentProduct({ssccExtensionDigit: e.target.value})}
                  placeholder="0"
                  required
                />
                <small className="form-hint">Single digit (0-9) for SSCC extension</small>
              </div>
              <div className="form-group">
                <label htmlFor="caseIndicatorDigit">Case Indicator Digit:</label>
                <input
                  type="tel"
                  id="caseIndicatorDigit"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength="1"
                  value={getCurrentProduct().caseIndicatorDigit}
                  onChange={(e) => updateCurrentProduct({caseIndicatorDigit: e.target.value})}
                  placeholder="0"
                  required
                />
                <small className="form-hint">Single digit (0-9) for case SGTINs</small>
              </div>
              {getCurrentProduct().useInnerCases && (
                <div className="form-group">
                  <label htmlFor="innerCaseIndicatorDigit">Inner Case Indicator Digit:</label>
                  <input
                    type="tel"
                    id="innerCaseIndicatorDigit"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength="1"
                    value={getCurrentProduct().innerCaseIndicatorDigit}
                    onChange={(e) => updateCurrentProduct({innerCaseIndicatorDigit: e.target.value})}
                    placeholder="0"
                    required
                  />
                  <small className="form-hint">Single digit (0-9) for inner case SGTINs</small>
                </div>
              )}
              <div className="form-group">
                <label htmlFor="itemIndicatorDigit">Item Indicator Digit:</label>
                <input
                  type="tel"
                  id="itemIndicatorDigit"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength="1"
                  value={getCurrentProduct().itemIndicatorDigit}
                  onChange={(e) => updateCurrentProduct({itemIndicatorDigit: e.target.value})}
                  placeholder="0"
                  required
                />
                <small className="form-hint">Single digit (0-9) for item SGTINs</small>
              </div>
            </div>
          </div>
        </div>
        
        <div className="hierarchy-section">
          <h3>Packaging Hierarchy (Product {activeProductIndex + 1})</h3>
          <div className="hierarchy-visual">
            <div className="hierarchy-level">
              <strong>SSCCs:</strong> {getCurrentProduct().numberOfSscc}
            </div>
            {getCurrentProduct().casesPerSscc === 0 ? (
              <>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Items per SSCC:</strong> {getCurrentProduct().itemsPerCase}
                </div>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Total Items:</strong> {calculateCurrentProductTotals().totalItems}
                </div>
              </>
            ) : (
              <>
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Cases:</strong> {calculateCurrentProductTotals().totalCases}
                </div>
                {getCurrentProduct().useInnerCases && (
                  <>
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Inner Cases:</strong> {calculateCurrentProductTotals().totalInnerCases}
                    </div>
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Items per Inner Case:</strong> {getCurrentProduct().itemsPerInnerCase}
                    </div>
                  </>
                )}
                {!getCurrentProduct().useInnerCases && (
                  <>
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Items per Case:</strong> {getCurrentProduct().itemsPerCase}
                    </div>
                  </>
                )}
                <div className="hierarchy-arrow">↓</div>
                <div className="hierarchy-level">
                  <strong>Total Items:</strong> {calculateCurrentProductTotals().totalItems}
                </div>
              </>
            )}
          </div>
          
          <div className="gs1-examples">
            <h4>GS1 Identifier Examples</h4>
            <p><strong>SSCC:</strong> urn:epc:id:sscc:{configuration.shipperCompanyPrefix}.{configuration.ssccExtensionDigit}[sscc_serial]</p>
            <p><strong>Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.caseIndicatorDigit}{configuration.productCode}.[case_serial]</p>
            {configuration.useInnerCases && (
              <p><strong>Inner Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.innerCaseIndicatorDigit}{configuration.productCode}.[inner_case_serial]</p>
            )}
            <p><strong>Item SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.itemIndicatorDigit}{configuration.productCode}.[item_serial]</p>
          </div>
        </div>
        
        <div className="config-actions">
          
          {/* <button 
            type="button" 
            onClick={handleSaveProgress} 
            disabled={isLoading} 
            className="btn-secondary"
          >
            Save Progress
          </button> */}
          <button 
            type="button" 
            onClick={handleSaveAndExit} 
            disabled={isLoading} 
            className="btn-outline"
          >
            Save & Exit
          </button>
          <button type="submit" disabled={isLoading} className="btn-primary">
            {isLoading ? 'Saving...' : 'Continue'}
            <FiChevronRight className="ml-2" />
          </button>
        </div>
      </form>
    </div>
  );

  const getCurrentContext = () => {
    const step = serialCollectionStep;
    const ssccNum = step.ssccIndex + 1;
    const caseNum = step.caseIndex + 1;
    const innerCaseNum = step.innerCaseIndex + 1;
    const itemNum = step.itemIndex + 1;
    
    switch (step.currentLevel) {
      case 'sscc':
        return {
          path: `SSCC ${ssccNum}`,
          label: 'SSCC Serial Number'
        };
      case 'case':
        return {
          path: `SSCC ${ssccNum} → Case ${caseNum}`,
          label: 'Case Serial Number'
        };
      case 'innerCase':
        return {
          path: `SSCC ${ssccNum} → Case ${caseNum} → Inner Case ${innerCaseNum}`,
          label: 'Inner Case Serial Number'
        };
      case 'item':
        const totalItems = getCurrentItemCount();
        if (configuration.useInnerCases) {
          return {
            path: `SSCC ${ssccNum} → Case ${caseNum} → Inner Case ${innerCaseNum} → Item ${itemNum} of ${totalItems}`,
            label: 'Item Serial Number'
          };
        } else if (configuration.casesPerSscc > 0) {
          return {
            path: `SSCC ${ssccNum} → Case ${caseNum} → Item ${itemNum} of ${totalItems}`,
            label: 'Item Serial Number'
          };
        } else {
          return {
            path: `SSCC ${ssccNum} → Item ${itemNum} of ${totalItems}`,
            label: 'Item Serial Number'
          };
        }
      default:
        return {
          path: 'Unknown',
          label: 'Serial Number'
        };
    }
  };

  const renderSerialTree = () => {
    console.log('Rendering tree with hierarchicalSerials:', hierarchicalSerials); // Debug log
    
    // Add safety check for hierarchicalSerials
    if (!hierarchicalSerials || !Array.isArray(hierarchicalSerials)) {
      console.error('hierarchicalSerials is undefined or not an array in renderSerialTree:', hierarchicalSerials);
      return (
        <div className="tree-view">
          <div className="error-message" style={{padding: '20px', textAlign: 'center', color: '#ef4444'}}>
            Serial numbers data is missing. Please reload the project.
          </div>
        </div>
      );
    }
    
    return (
      <div className="tree-view">
        {hierarchicalSerials.map((ssccData, ssccIndex) => (
          <div key={ssccIndex} className="tree-level sscc-level">
            <div className="tree-item">
              <div className="tree-icon"><FiPackage /></div>
              <div className="tree-label">SSCC {ssccIndex + 1}</div>
              <div className={`tree-serial ${ssccData.ssccSerial ? 'completed' : ''} ${isCurrentPosition('sscc', ssccIndex) ? 'current' : ''}`} 
                   onClick={() => handleEditSerial(`sscc-${ssccIndex}`, ssccData.ssccSerial)}>
                {ssccData.ssccSerial || (
                  <span className="empty-serial">Click to add</span>
                )}
              </div>
            </div>
            
            {/* Cases */}
            {ssccData.cases && ssccData.cases.length > 0 && ssccData.cases.map((caseData, caseIndex) => (
              <div key={caseIndex} className="tree-level case-level">
                <div className="tree-item">
                  <div className="tree-icon"><FiBox /></div>
                  <div className="tree-label">Case {caseIndex + 1}</div>
                  <div className={`tree-serial ${caseData.caseSerial ? 'completed' : ''} ${isCurrentPosition('case', ssccIndex, caseIndex) ? 'current' : ''}`}
                       onClick={() => handleEditSerial(`case-${ssccIndex}-${caseIndex}`, caseData.caseSerial)}>
                    {caseData.caseSerial || (
                      <span className="empty-serial">Click to add</span>
                    )}
                  </div>
                </div>
                
                {/* Inner Cases */}
                {caseData.innerCases && caseData.innerCases.length > 0 && caseData.innerCases.map((innerCaseData, innerCaseIndex) => (
                  <div key={innerCaseIndex} className="tree-level inner-case-level">
                    <div className="tree-item">
                      <div className="tree-icon"><FiFolder /></div>
                      <div className="tree-label">Inner Case {innerCaseIndex + 1}</div>
                      <div className={`tree-serial ${innerCaseData.innerCaseSerial ? 'completed' : ''} ${isCurrentPosition('innerCase', ssccIndex, caseIndex, innerCaseIndex) ? 'current' : ''}`}
                           onClick={() => handleEditSerial(`innerCase-${ssccIndex}-${caseIndex}-${innerCaseIndex}`, innerCaseData.innerCaseSerial)}>
                        {innerCaseData.innerCaseSerial || (
                          <span className="empty-serial">Click to add</span>
                        )}
                      </div>
                    </div>
                    
                    {/* Items in Inner Cases */}
                    {innerCaseData.items && innerCaseData.items.length > 0 && (
                      <div className="items-container">
                        {innerCaseData.items.map((itemData, itemIndex) => (
                          <div key={itemIndex} className="tree-level item-level">
                            <div className="tree-item">
                              <div className="tree-icon"><FiFile /></div>
                              <div className="tree-label">Item {itemIndex + 1} of {innerCaseData.items.length}</div>
                              <div className={`tree-serial ${itemData.itemSerial ? 'completed' : ''} ${isCurrentPosition('item', ssccIndex, caseIndex, innerCaseIndex, itemIndex) ? 'current' : ''}`}
                                   onClick={() => handleEditSerial(`item-${ssccIndex}-${caseIndex}-${innerCaseIndex}-${itemIndex}`, itemData.itemSerial)}>
                                {itemData.itemSerial || (
                                  <span className="empty-serial">Click to add</span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Items in Cases (no inner cases) */}
                {(!caseData.innerCases || caseData.innerCases.length === 0) && caseData.items && caseData.items.length > 0 && (
                  <div className="items-container">
                    {caseData.items.map((itemData, itemIndex) => (
                      <div key={itemIndex} className="tree-level item-level">
                        <div className="tree-item">
                          <div className="tree-icon"><FiFile /></div>
                          <div className="tree-label">Item {itemIndex + 1} of {caseData.items.length}</div>
                          <div className={`tree-serial ${itemData.itemSerial ? 'completed' : ''} ${isCurrentPosition('item', ssccIndex, caseIndex, null, itemIndex) ? 'current' : ''}`}
                               onClick={() => handleEditSerial(`item-${ssccIndex}-${caseIndex}-${itemIndex}`, itemData.itemSerial)}>
                            {itemData.itemSerial || (
                              <span className="empty-serial">Click to add</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {/* Items directly in SSCC (no cases) */}
            {(!ssccData.cases || ssccData.cases.length === 0) && ssccData.items && ssccData.items.length > 0 && (
              <div className="items-container">
                {ssccData.items.map((itemData, itemIndex) => (
                  <div key={itemIndex} className="tree-level item-level">
                    <div className="tree-item">
                      <div className="tree-icon"><FiFile /></div>
                      <div className="tree-label">Item {itemIndex + 1} of {ssccData.items.length}</div>
                      <div className={`tree-serial ${itemData.itemSerial ? 'completed' : ''} ${isCurrentPosition('item', ssccIndex, null, null, itemIndex) ? 'current' : ''}`}
                           onClick={() => handleEditSerial(`item-${ssccIndex}-${itemIndex}`, itemData.itemSerial)}>
                        {itemData.itemSerial || (
                          <span className="empty-serial">Click to add</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const isCurrentPosition = (level, ssccIndex, caseIndex = null, innerCaseIndex = null, itemIndex = null) => {
    const step = serialCollectionStep;
    return step.currentLevel === level && 
           step.ssccIndex === ssccIndex && 
           (caseIndex === null || step.caseIndex === caseIndex) &&
           (innerCaseIndex === null || step.innerCaseIndex === innerCaseIndex) &&
           (itemIndex === null || step.itemIndex === itemIndex);
  };

  const isCurrentContainer = (level, ssccIndex, caseIndex = null, innerCaseIndex = null) => {
    const step = serialCollectionStep;
    // Check if this is the current container being filled
    if (level === 'sscc' && step.ssccIndex === ssccIndex) {
      return true;
    }
    if (level === 'case' && step.ssccIndex === ssccIndex && step.caseIndex === caseIndex) {
      return true;
    }
    if (level === 'innerCase' && step.ssccIndex === ssccIndex && step.caseIndex === caseIndex && step.innerCaseIndex === innerCaseIndex) {
      return true;
    }
    return false;
  };

  const getCurrentItemCount = () => {
    const casesPerSscc = parseInt(configuration.casesPerSscc) || 0;
    const itemsPerCase = parseInt(configuration.itemsPerCase) || 0;
    const itemsPerInnerCase = parseInt(configuration.itemsPerInnerCase) || 0;
    const useInnerCases = configuration.useInnerCases;
    
    console.log('getCurrentItemCount - Configuration values:', {
      casesPerSscc,
      itemsPerCase,
      itemsPerInnerCase,
      useInnerCases
    });
    
    if (useInnerCases) {
      console.log('getCurrentItemCount - Using inner cases, returning:', itemsPerInnerCase);
      return itemsPerInnerCase;
    } else if (casesPerSscc > 0) {
      console.log('getCurrentItemCount - Using cases, returning:', itemsPerCase);
      return itemsPerCase;
    } else {
      console.log('getCurrentItemCount - Direct SSCC->Items, returning:', itemsPerCase);
      return itemsPerCase;
    }
  };

  // Function to convert flat serial format back to hierarchical format (for fixing corrupted projects)
  const convertFlatToHierarchical = (flatData, config) => {
    console.log('Converting flat data to hierarchical:', { flatData, config });
    
    if (!flatData || !Array.isArray(flatData) || flatData.length === 0) {
      return [];
    }
    
    // Check if data is already in hierarchical format
    if (flatData[0] && typeof flatData[0] === 'object' && 
        (flatData[0].hasOwnProperty('ssccSerial') || flatData[0].hasOwnProperty('cases') || flatData[0].hasOwnProperty('items'))) {
      console.log('Data is already in hierarchical format');
      return flatData;
    }
    
    // Extract serials by type
    const ssccSerials = flatData.filter(item => item.type === 'sscc').map(item => item.serial);
    const caseSerials = flatData.filter(item => item.type === 'case').map(item => item.serial);
    const innerCaseSerials = flatData.filter(item => item.type === 'inner_case').map(item => item.serial);
    const itemSerials = flatData.filter(item => item.type === 'item').map(item => item.serial);
    
    console.log('Extracted serials:', { ssccSerials, caseSerials, innerCaseSerials, itemSerials });
    
    const hierarchicalData = [];
    
    for (let ssccIndex = 0; ssccIndex < config.numberOfSscc; ssccIndex++) {
      const ssccData = {
        ssccSerial: ssccSerials[ssccIndex] || '',
        cases: []
      };
      
      if (config.casesPerSscc === 0) {
        // Direct SSCC → Items
        ssccData.items = [];
        for (let itemIndex = 0; itemIndex < config.itemsPerCase; itemIndex++) {
          const globalItemIndex = ssccIndex * config.itemsPerCase + itemIndex;
          ssccData.items.push({
            itemSerial: itemSerials[globalItemIndex] || ''
          });
        }
      } else {
        // SSCC → Cases
        for (let caseIndex = 0; caseIndex < config.casesPerSscc; caseIndex++) {
          const globalCaseIndex = ssccIndex * config.casesPerSscc + caseIndex;
          const caseData = {
            caseSerial: caseSerials[globalCaseIndex] || '',
            innerCases: [],
            items: []
          };
          
          if (config.useInnerCases) {
            // Cases → Inner Cases → Items
            for (let innerCaseIndex = 0; innerCaseIndex < config.innerCasesPerCase; innerCaseIndex++) {
              const globalInnerCaseIndex = globalCaseIndex * config.innerCasesPerCase + innerCaseIndex;
              const innerCaseData = {
                innerCaseSerial: innerCaseSerials[globalInnerCaseIndex] || '',
                items: []
              };
              
              for (let itemIndex = 0; itemIndex < config.itemsPerInnerCase; itemIndex++) {
                const globalItemIndex = globalInnerCaseIndex * config.itemsPerInnerCase + itemIndex;
                innerCaseData.items.push({
                  itemSerial: itemSerials[globalItemIndex] || ''
                });
              }
              
              caseData.innerCases.push(innerCaseData);
            }
          } else {
            // Cases → Items directly
            for (let itemIndex = 0; itemIndex < config.itemsPerCase; itemIndex++) {
              const globalItemIndex = globalCaseIndex * config.itemsPerCase + itemIndex;
              caseData.items.push({
                itemSerial: itemSerials[globalItemIndex] || ''
              });
            }
          }
          
          ssccData.cases.push(caseData);
        }
      }
      
      hierarchicalData.push(ssccData);
    }
    
    console.log('Converted to hierarchical format:', hierarchicalData);
    return hierarchicalData;
  };

  const renderStep2 = () => {
    // Re-initialize hierarchical serials ONLY for completed projects with missing data
    // Do NOT interfere with new projects or projects in progress
    if (currentProject && 
        currentProject.status === 'Completed' && 
        currentProject.serial_numbers && 
        currentProject.serial_numbers.length > 0 &&
        (!hierarchicalSerials || hierarchicalSerials.length === 0)) {
      
      console.log('Re-initializing hierarchical serials for completed project with missing state');
      
      // Check if the data needs conversion from flat format to hierarchical
      const convertedData = convertFlatToHierarchical(currentProject.serial_numbers, currentProject.configuration);
      setHierarchicalSerials(convertedData);
      
      // Also ensure serial collection step is marked as complete
      if (currentProject.configuration) {
        const currentPosition = findCurrentSerialPosition(convertedData, currentProject.configuration);
        setSerialCollectionStep({
          ...currentPosition,
          isComplete: true
        });
      }
    }
    
    // Check if current hierarchicalSerials is in flat format and needs conversion
    // But ONLY for completed projects, not new ones
    if (hierarchicalSerials && 
        hierarchicalSerials.length > 0 && 
        currentProject && 
        currentProject.status === 'Completed' &&
        currentProject.configuration) {
      
      const firstItem = hierarchicalSerials[0];
      if (firstItem && typeof firstItem === 'object' && firstItem.type && firstItem.serial) {
        console.log('Detected flat format in completed project hierarchicalSerials, converting...');
        const convertedData = convertFlatToHierarchical(hierarchicalSerials, currentProject.configuration);
        setHierarchicalSerials(convertedData);
        
        // Update serial collection step
        const currentPosition = findCurrentSerialPosition(convertedData, currentProject.configuration);
        setSerialCollectionStep({
          ...currentPosition,
          isComplete: true
        });
      }
    }
    const totals = calculateTotals();
    
    if (serialCollectionStep.isComplete) {
      // Show summary and submit button
      return (
        <div className="step-container">
          <h2 className="step-title">Step 2: Serial Numbers - Complete</h2>
          
          <div className="completion-summary">
            <h3>✅ All Serial Numbers Collected</h3>
            <p>You have successfully entered all {totals.totalItems} item serial numbers and their parent container serial numbers.</p>
            
            <div className="summary-stats">
              <div className="stat">
                <strong>SSCCs:</strong> {configuration.numberOfSscc}
              </div>
              {totals.totalCases > 0 && (
                <div className="stat">
                  <strong>Cases:</strong> {totals.totalCases}
                </div>
              )}
              {totals.totalInnerCases > 0 && (
                <div className="stat">
                  <strong>Inner Cases:</strong> {totals.totalInnerCases}
                </div>
              )}
              <div className="stat">
                <strong>Items:</strong> {totals.totalItems}
              </div>
            </div>
          </div>
          
          {/* Visual Tree Component */}
          <div className="serial-tree-container">
            <h3>Serial Number Overview</h3>
            <div className="serial-tree">
              {renderSerialTree()}
            </div>
          </div>
          
          <div className="button-group">
            <button 
              type="button" 
              onClick={() => {
                // Check if there are any serial numbers entered
                const hasSerialNumbers = hierarchicalSerials && hierarchicalSerials.some(sscc => 
                  sscc.ssccSerial || 
                  (sscc.cases && sscc.cases.some(c => c.caseSerial || (c.items && c.items.some(i => i.itemSerial)))) ||
                  (sscc.items && sscc.items.some(i => i.itemSerial))
                );
                
                // Set packaging configuration lock if there are serial numbers
                if (hasSerialNumbers) {
                  setIsPackagingConfigLocked(true);
                  setOriginalPackagingConfig({
                    itemsPerCase: configuration.itemsPerCase,
                    casesPerSscc: configuration.casesPerSscc,
                    numberOfSscc: configuration.numberOfSscc,
                    useInnerCases: configuration.useInnerCases,
                    innerCasesPerCase: configuration.innerCasesPerCase,
                    itemsPerInnerCase: configuration.itemsPerInnerCase
                  });
                }
                
                setCurrentStep(1);
                scrollToTop();
              }} 
              className="btn-secondary"
            >
              Back
            </button>
            <button 
              type="button" 
              onClick={handleSaveAndExit} 
              disabled={isLoading} 
              className="btn-outline"
            >
              Save & Exit
            </button>
            <button 
              type="button" 
              onClick={handleSerialNumbersSubmit}
              disabled={isLoading} 
              className="btn-primary"
            >
              {isLoading ? 'Saving...' : 'Save Serial Numbers'}
            </button>
            {/* <button 
              type="button" 
              onClick={handleSaveProgress} 
              disabled={isLoading} 
              className="btn-secondary"
              style={{ marginLeft: '10px' }}
            >
              Save Progress
            </button> */}
            
          </div>
        </div>
      );
    }
    
    // Show current serial input
    const currentContext = getCurrentContext();
    
    return (
      <div className="step-container">
        <h2 className="step-title">Step 2: Serial Numbers</h2>
        
        <div className="hierarchical-input">
          <div className="current-input">
            <div className="context-path">
              {renderClickableContext(currentContext.path)}
            </div>
            {/* <h5>Enter {currentContext.label}:</h5> */}
            <div className="input-group">
              {serialCollectionStep.currentLevel === 'item' ? (
                <textarea
                  value={serialCollectionStep.currentSerial}
                  onChange={(e) => handleSerialInput(e.target.value)}
                  placeholder={`Enter ${currentContext.label} serial numbers, one per line`}
                  className="serial-textarea"
                  rows="4"
                  autoFocus
                />
              ) : (
                <input
                  type="text"
                  value={serialCollectionStep.currentSerial}
                  onChange={(e) => handleSerialInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleNextSerial();
                    }
                  }}
                  placeholder={`Enter ${currentContext.label} serial number`}
                  className="serial-input"
                  autoFocus
                />
              )}
              {serialCollectionStep.currentLevel !== 'sscc' && (
                <button
                  type="button"
                  className="scan-button"
                  onClick={() => openScanner('current', null)}
                  title="Scan barcode"
                >
                  <FiCamera size={20} />
                </button>
              )}
            </div>
          </div>
          
          <div className="progress-info">
              <p className="mb-2">Current position in the process:</p>
            <div className="progress-stats">
              <div className={`stat ${serialCollectionStep.currentLevel === 'sscc' ? 'stat-current' : ''}`}>
                <strong>SSCC:</strong> {serialCollectionStep.ssccIndex + 1} of {configuration.numberOfSscc}
              </div>
              {configuration.casesPerSscc > 0 && (
                <div className={`stat ${serialCollectionStep.currentLevel === 'case' ? 'stat-current' : ''}`}>
                  <strong>Case:</strong> {serialCollectionStep.caseIndex + 1} of {configuration.casesPerSscc}
                </div>
              )}
              {configuration.useInnerCases && (
                <div className={`stat ${serialCollectionStep.currentLevel === 'innerCase' ? 'stat-current' : ''}`}>
                  <strong>Inner Case:</strong> {serialCollectionStep.innerCaseIndex + 1} of {configuration.innerCasesPerCase}
                </div>
              )}
              <div className={`stat ${serialCollectionStep.currentLevel === 'item' ? 'stat-current' : ''}`}>
                <strong>Item:</strong> {serialCollectionStep.itemIndex + 1} of {getCurrentItemCount()}
              </div>
            </div>
          </div>
          
          <div className="button-group">
            <button 
              type="button" 
              onClick={() => {
                // Check if there are any serial numbers entered
                const hasSerialNumbers = hierarchicalSerials && hierarchicalSerials.some(sscc => 
                  sscc.ssccSerial || 
                  (sscc.cases && sscc.cases.some(c => c.caseSerial || (c.items && c.items.some(i => i.itemSerial)))) ||
                  (sscc.items && sscc.items.some(i => i.itemSerial))
                );
                
                // Set packaging configuration lock if there are serial numbers
                if (hasSerialNumbers) {
                  setIsPackagingConfigLocked(true);
                  setOriginalPackagingConfig({
                    itemsPerCase: configuration.itemsPerCase,
                    casesPerSscc: configuration.casesPerSscc,
                    numberOfSscc: configuration.numberOfSscc,
                    useInnerCases: configuration.useInnerCases,
                    innerCasesPerCase: configuration.innerCasesPerCase,
                    itemsPerInnerCase: configuration.itemsPerInnerCase
                  });
                }
                
                setCurrentStep(1);
                scrollToTop();
              }} 
              className="btn-secondary"
            >
              Back
            </button>
            <button 
              type="button" 
              onClick={handleSaveAndExit} 
              disabled={isLoading} 
              className="btn-outline"
            >
              Save & Exit
            </button>
            <button 
              type="button" 
              onClick={handleNextSerial}
              disabled={!serialCollectionStep.currentSerial.trim()}
              className="btn-primary"
            >
              Next
            </button>
            {/* <button 
              type="button" 
              onClick={handleSaveProgress} 
              disabled={isLoading} 
              className="btn-secondary"
              style={{ marginLeft: '10px' }}
            >
              Save Progress
            </button> */}
            
          </div>
        </div>
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
                <span className="epcis-value">EPCIS 1.2</span>
              </div>
              <div className="epcis-row">
                <span className="epcis-label">Event Types</span>
                <span className="epcis-value">Object, Aggregation</span>
              </div>
              <div className="epcis-row">
                <span className="epcis-label">Business Step</span>
                <span className="epcis-value">Commissioning, Packing, Shipping</span>
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
          <button 
            type="button" 
            onClick={handleSaveAndExit} 
            disabled={isLoading} 
            className="btn-outline"
          >
            Save & Exit
          </button>
          <button onClick={handleGenerateEPCIS} disabled={isLoading} className="btn-primary">
            {isLoading ? 'Generating...' : 'Generate & Download EPCIS'}
          </button>
          {/* <button 
            type="button" 
            onClick={handleSaveProgress} 
            disabled={isLoading} 
            className="btn-secondary"
            style={{ marginLeft: '10px' }}
          >
            Save Progress
          </button> */}
          
        </div>
      </div>
    );
  };

  return (
    <AuthWrapper>
      {showDashboard ? (
        <ProjectDashboard 
          onSelectProject={handleSelectProject}
          onLogout={handleLogout}
        />
      ) : (
        <div className="app">
          <div className="container">
            <header className="header">
              <div className="header-content">
              {currentProject && (
                <div className="progress-bar">
                  <div>
                    
                  <div className="project-progress-header">
                    <h2 className="project-name">{currentProject.name}</h2>
                    {isAutoSaving && (
                      <div className="auto-save-indicator">
                        <span className="auto-save-spinner"></span>
                      </div>
                    )}
                  </div>
                  <button 
                    type="button" 
                    onClick={handleSaveAndExit} 
                    disabled={isLoading} 
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-md font-medium"
                    >
                    Save & Exit
                    </button>
                  </div>
                  <div className="progress-steps">
                    <div className={`step ${currentStep === 1 ? 'active' : currentStep > 1 ? 'completed' : ''}`}>
                      <span className="step-number">1</span>
                      <span className="step-label">Configuration</span>
                    </div>
                    <div className={`step ${currentStep === 2 ? 'active' : currentStep > 2 ? 'completed' : ''}`}>
                      <span className="step-number">2</span>
                      <span className="step-label">Serial Numbers</span>
                    </div>
                    <div className={`step ${currentStep === 3 ? 'active' : ''}`}>
                      <span className="step-number">3</span>
                      <span className="step-label">Generate EPCIS</span>
                    </div>
                  </div>
                </div>
              )}
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
                  {/* ScandIt Scanner Container - replaces old video element */}
                  <div ref={scannerContainerRef} className="scandit-scanner" style={{width: '100%', height: '100%', minHeight: '400px'}}></div>
                  {isScanning && (
                    <div className="scanning-overlay">
                      <div className="scanning-frame"></div>
                      <p className="scanning-text">Scanning for 2D Data Matrix codes only...</p>
                    </div>
                  )}
                </div>
                
                {/* Multi-scanning progress */}
                {requiredItemCount > 1 && (
                  <div className="scanning-progress">
                    <h4>Scanning Items ({scannedItems.length} of {requiredItemCount})</h4>
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ width: `${(scannedItems.length / requiredItemCount) * 100}%` }}
                      ></div>
                    </div>
                    {scannedItems.length > 0 && (
                      <div className="scanned-items-preview">
                        <p className="preview-label">Scanned items (tap "x" to remove):</p>
                        <ul className="scanned-items-list">
                          {scannedItems.map((item, index) => (
                            <li key={index} className="scanned-item">
                              <div className="scanned-item-info">
                                <span className="item-number">{index + 1}.</span>
                                <span className="item-serial">{item}</span>
                              <button
                                onClick={() => removeScannedItem(index)}
                                className="remove-item-btn"
                                title={`Remove item ${index + 1}: ${item}`}
                              >
                                ✕
                              </button>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                
                {!isScanning && (
                  <div className="scanner-instructions">
                    <p className="error-text">Camera not started. Please check permissions.</p>
                  </div>
                )}
              </div>
              <div className="scanner-footer">
                {requiredItemCount > 1 && scannedItems.length > 0 && (
                  <button 
                    className="btn-primary ml-2" 
                    onClick={() => {
                      const itemsText = scannedItems.join('\n');
                      setSerialCollectionStep({
                        ...serialCollectionStep,
                        currentSerial: itemsText
                      });
                      setSuccess(`Saved ${scannedItems.length} scanned items`);
                      closeScanner();
                    }}
                  >
                    Save {scannedItems.length} Items
                  </button>
                )}
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
                        <div className="fda-packaging-info">
                          <div className="packaging-header">
                            <strong>Package NDC:</strong> {productOption.packageNdc}
                          </div>
                          <div className="packaging-description">
                            <strong>Package Description:</strong> {productOption.packageDescription}
                          </div>
                        </div>
                        <div className="fda-product-details">
                          <p><strong>Manufacturer:</strong> {productOption.labeler_name}</p>
                          <p><strong>Dosage Form:</strong> {productOption.dosage_form}</p>
                          {productOption.active_ingredients && (
                            <p><strong>Active Ingredients:</strong> {productOption.active_ingredients.map(ing => `${ing.name} ${ing.strength}`).join(', ')}</p>
                          )}
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

        {/* Edit Serial Modal */}
        {editModal.isOpen && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>Edit Serial Number</h3>
                <button className="close-button" onClick={handleCancelEdit}>
                  <FiX />
                </button>
              </div>
              <div className="modal-body">
                <div className="edit-context">
                  <h4>{editModal.label}</h4>
                  <p className="context-path">{editModal.contextPath}</p>
                </div>
                <div className="edit-input-group">
                  <input
                    type="text"
                    value={editModal.currentValue}
                    onChange={(e) => {
                      const newValue = e.target.value;
                      // Check for duplicates as user types
                      const duplicates = validateDuplicateSerials(newValue, editModal.path);
                      if (duplicates && newValue.trim()) {
                        setError(`Duplicate serial number found! "${newValue}" is already used at: ${duplicates[0].path}`);
                      } else {
                        setError('');
                      }
                      setEditModal({...editModal, currentValue: newValue});
                    }}
                    placeholder={`Enter ${editModal.label}`}
                    className="edit-serial-input"
                    autoFocus
                  />
                  <button
                    type="button"
                    className="scan-button"
                    onClick={() => {
                      setScannerModal({ isOpen: true, targetField: 'edit', targetSetter: null });
                    }}
                    title="Scan barcode"
                  >
                    <FiCamera size={20} />
                  </button>
                </div>
                <div className="modal-actions">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveEditedSerial}
                    disabled={!editModal.currentValue.trim()}
                    className="btn-primary"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Location Selector Modal */}
        <LocationSelector 
          isOpen={locationSelectorModal.isOpen}
          onClose={closeLocationSelector}
          onSelectLocation={handleLocationSelected}
          targetSection={locationSelectorModal.targetSection}
        />
          </div>
          <div className="footer-wrapper"><img className="logo" src="https://rxerp.com/wp-content/uploads/2025/01/rxerp-logo-hero-tagline.svg"></img></div>
        </div>
      )}
    </AuthWrapper>
  );
}

export default App;