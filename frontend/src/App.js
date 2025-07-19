import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { BrowserMultiFormatReader } from '@zxing/browser';
import { BarcodeFormat } from '@zxing/library';
import { FiCamera, FiChevronRight, FiPackage, FiBox, FiFolder, FiFile, FiX, FiArrowLeft } from 'react-icons/fi';
import { useAuth } from './AuthContext';
import AuthWrapper from './AuthWrapper';
import ProjectDashboard from './ProjectDashboard';

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
  const [configuration, setConfiguration] = useState({
    itemsPerCase: '',
    casesPerSscc: '',
    numberOfSscc: '',
    useInnerCases: false,
    innerCasesPerCase: '',
    itemsPerInnerCase: '',
    companyPrefix: '0345802',
    productCode: '46653',
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
  const [scannerModal, setScannerModal] = useState({ isOpen: false, targetField: '', targetSetter: null });
  const [scannedItems, setScannedItems] = useState([]);
  const [requiredItemCount, setRequiredItemCount] = useState(1);
  const [shouldContinueScanning, setShouldContinueScanning] = useState(false);
  const [fdaModal, setFdaModal] = useState({ isOpen: false, searchResults: [], isLoading: false });
  const [editModal, setEditModal] = useState({ isOpen: false, path: '', currentValue: '', label: '', contextPath: '' });
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const [autoSaveTimer, setAutoSaveTimer] = useState(null);
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
    setCurrentProject(project);
    setShowDashboard(false);
    setHasUnsavedChanges(false); // Reset unsaved changes flag
    
    // Reset packaging configuration lock state for new project selection
    setIsPackagingConfigLocked(false);
    setOriginalPackagingConfig(null);
    
    // Helper function to get configuration value (handles both camelCase and snake_case)
    const getConfigValue = (config, camelKey, snakeKey, defaultValue) => {
      return config[camelKey] || config[snakeKey] || defaultValue;
    };
    
    // Helper function to get numeric configuration value
    const getNumericConfigValue = (config, camelKey, snakeKey, defaultValue) => {
      const value = config[camelKey] || config[snakeKey] || defaultValue;
      return parseInt(value) || defaultValue;
    };
    
    // Load project configuration
    if (project.configuration) {
      const config = project.configuration;
      console.log('Loading project configuration:', config);
      setConfiguration({
        itemsPerCase: getNumericConfigValue(config, 'itemsPerCase', 'items_per_case', 10),
        casesPerSscc: getNumericConfigValue(config, 'casesPerSscc', 'cases_per_sscc', 5),
        numberOfSscc: getNumericConfigValue(config, 'numberOfSscc', 'number_of_sscc', 1),
        useInnerCases: getConfigValue(config, 'useInnerCases', 'use_inner_cases', false),
        innerCasesPerCase: getNumericConfigValue(config, 'innerCasesPerCase', 'inner_cases_per_case', 2),
        itemsPerInnerCase: getNumericConfigValue(config, 'itemsPerInnerCase', 'items_per_inner_case', 5),
        companyPrefix: getConfigValue(config, 'companyPrefix', 'company_prefix', '0345802'),
        productCode: getConfigValue(config, 'productCode', 'product_code', '46653'),
        lotNumber: getConfigValue(config, 'lotNumber', 'lot_number', ''),
        expirationDate: getConfigValue(config, 'expirationDate', 'expiration_date', ''),
        ssccExtensionDigit: getConfigValue(config, 'ssccExtensionDigit', 'sscc_extension_digit', '0'),
        caseIndicatorDigit: getConfigValue(config, 'caseIndicatorDigit', 'case_indicator_digit', '0'),
        innerCaseIndicatorDigit: getConfigValue(config, 'innerCaseIndicatorDigit', 'inner_case_indicator_digit', '0'),
        itemIndicatorDigit: getConfigValue(config, 'itemIndicatorDigit', 'item_indicator_digit', '0'),
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
        shipperSameAsSender: getConfigValue(config, 'shipperSameAsSender', 'shipper_same_as_sender', false),
        // EPCClass data
        productNdc: getConfigValue(config, 'productNdc', 'product_ndc', ''),
        packageNdc: getConfigValue(config, 'packageNdc', 'package_ndc', ''),
        regulatedProductName: getConfigValue(config, 'regulatedProductName', 'regulated_product_name', ''),
        manufacturerName: getConfigValue(config, 'manufacturerName', 'manufacturer_name', ''),
        dosageFormType: getConfigValue(config, 'dosageFormType', 'dosage_form_type', ''),
        strengthDescription: getConfigValue(config, 'strengthDescription', 'strength_description', ''),
        netContentDescription: getConfigValue(config, 'netContentDescription', 'net_content_description', '')
      });
    }
    
    // Set current step based on project state
    setCurrentStep(project.current_step);
    
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
      
      // Also restore the serial collection step state if we're on step 2
      if (project.current_step === 2 && project.configuration) {
        // Find the current position in the serial collection
        const currentPosition = findCurrentSerialPosition(project.serial_numbers, project.configuration);
        if (currentPosition.isComplete) {
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
      companyPrefix: '0345802',
      productCode: '46653',
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
    
    // Reset serial number states
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
      const updateData = {
        current_step: currentStep,
        updated_at: new Date().toISOString()
      };

      // Save configuration if we're on step 1 or beyond
      if (currentStep >= 1) {
        updateData.configuration = {
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
      { field: 'casesPerSscc', value: configuration.casesPerSscc, name: 'Cases per SSCC' },
      { field: 'companyPrefix', value: configuration.companyPrefix, name: 'Company Prefix' },
      { field: 'productCode', value: configuration.productCode, name: 'Product Code' },
      { field: 'ssccExtensionDigit', value: configuration.ssccExtensionDigit, name: 'SSCC Extension Digit' },
      { field: 'caseIndicatorDigit', value: configuration.caseIndicatorDigit, name: 'Case Indicator Digit' },
      { field: 'itemIndicatorDigit', value: configuration.itemIndicatorDigit, name: 'Item Indicator Digit' }
    ];
    
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
      
      // If we have existing serial numbers, auto-save them with the new configuration
      if (hierarchicalSerials && hierarchicalSerials.length > 0) {
        autoSaveSerialNumbers(hierarchicalSerials);
      }
      
      setCurrentStep(2);
      
      // Set appropriate success message
      if (hierarchicalSerials && hierarchicalSerials.length > 0) {
        setSuccess('Configuration saved successfully! Your previously entered serial numbers have been preserved.');
      } else {
        setSuccess('Configuration saved successfully!');
      }
      
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
    
    try {
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
  const validateDuplicateSerials = (newSerial, currentPath) => {
    const allSerials = [];
    
    // Normalize the serial number (trim whitespace, convert to lowercase for comparison)
    const normalizedNewSerial = newSerial.trim().toLowerCase();
    
    if (!normalizedNewSerial) {
      return null; // Empty serials are not duplicates
    }
    
    // Collect all existing serials
    hierarchicalSerials.forEach((ssccData, ssccIndex) => {
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
          if (caseData.caseSerial && caseData.caseSerial.trim()) {
            allSerials.push({
              serial: caseData.caseSerial.trim(),
              normalizedSerial: caseData.caseSerial.trim().toLowerCase(),
              path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1}`,
              isCurrentPath: currentPath === `case-${ssccIndex}-${caseIndex}`
            });
          }
          
          if (caseData.innerCases) {
            caseData.innerCases.forEach((innerCaseData, innerCaseIndex) => {
              if (innerCaseData.innerCaseSerial && innerCaseData.innerCaseSerial.trim()) {
                allSerials.push({
                  serial: innerCaseData.innerCaseSerial.trim(),
                  normalizedSerial: innerCaseData.innerCaseSerial.trim().toLowerCase(),
                  path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1} → Inner Case ${innerCaseIndex + 1}`,
                  isCurrentPath: currentPath === `innerCase-${ssccIndex}-${caseIndex}-${innerCaseIndex}`
                });
              }
              
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
            });
          } else {
            caseData.items.forEach((itemData, itemIndex) => {
              if (itemData.itemSerial && itemData.itemSerial.trim()) {
                allSerials.push({
                  serial: itemData.itemSerial.trim(),
                  normalizedSerial: itemData.itemSerial.trim().toLowerCase(),
                  path: `SSCC ${ssccIndex + 1} → Case ${caseIndex + 1} → Item ${itemIndex + 1}`,
                  isCurrentPath: currentPath === `item-${ssccIndex}-${caseIndex}-${itemIndex}`
                });
              }
            });
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
    
    // Check for duplicates using normalized comparison
    const duplicates = allSerials.filter(item => 
      item.normalizedSerial === normalizedNewSerial && !item.isCurrentPath
    );
    
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
    
    // Save current serial before navigating
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
      
      // Update the hierarchical data with current changes
      setHierarchicalSerials(currentHierarchicalData);
    }
    
    // Parse the clicked level to determine position and restore previous value
    const step = serialCollectionStep;
    
    if (clickedLevel.includes('SSCC')) {
      // Navigate to SSCC level
      const currentSSCC = currentHierarchicalData[step.ssccIndex];
      setSerialCollectionStep({
        ...step,
        currentLevel: 'sscc',
        currentSerial: currentSSCC.ssccSerial || '',
        caseIndex: 0,
        innerCaseIndex: 0,
        itemIndex: 0,
        isComplete: false
      });
    } else if (clickedLevel.includes('Case') && !clickedLevel.includes('Inner')) {
      // Navigate to Case level
      const currentCase = currentHierarchicalData[step.ssccIndex].cases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex];
      setSerialCollectionStep({
        ...step,
        currentLevel: 'case',
        currentSerial: currentCase ? (currentCase.caseSerial || '') : '',
        innerCaseIndex: 0,
        itemIndex: 0,
        isComplete: false
      });
    } else if (clickedLevel.includes('Inner Case')) {
      // Navigate to Inner Case level
      const currentInnerCase = currentHierarchicalData[step.ssccIndex].cases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex] && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex].innerCases && currentHierarchicalData[step.ssccIndex].cases[step.caseIndex].innerCases[step.innerCaseIndex];
      setSerialCollectionStep({
        ...step,
        currentLevel: 'innerCase',
        currentSerial: currentInnerCase ? (currentInnerCase.innerCaseSerial || '') : '',
        itemIndex: 0,
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
      
      // Validate all serials for duplicates
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
          
          const duplicates = validateDuplicateSerials(serial, tempPath);
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
        currentSerial: ''
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
        currentSerial: ''
      });
    }
    
    setError('');
  };

  const calculateNextStep = (itemsToSkip = 0) => {
    const current = serialCollectionStep;
    const totals = calculateTotals();
    
    if (current.currentLevel === 'sscc') {
      // Move to first case or first item (if direct SSCC→Items)
      if (configuration.casesPerSscc === 0) {
        return {
          ...current,
          currentLevel: 'item',
          itemIndex: 0
        };
      } else {
        return {
          ...current,
          currentLevel: 'case',
          caseIndex: 0
        };
      }
    } else if (current.currentLevel === 'case') {
      // Move to first inner case or first item
      if (configuration.useInnerCases) {
        return {
          ...current,
          currentLevel: 'innerCase',
          innerCaseIndex: 0
        };
      } else {
        return {
          ...current,
          currentLevel: 'item',
          itemIndex: 0
        };
      }
    } else if (current.currentLevel === 'innerCase') {
      // Move to first item in this inner case
      return {
        ...current,
        currentLevel: 'item',
        itemIndex: 0
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
    
    // Clear multi-scanning state
    setScannedItems([]);
    setRequiredItemCount(1);
    setShouldContinueScanning(false);
    
    setScannerModal({ isOpen: false, targetField: '', targetSetter: null });
  };

  const startScanning = async () => {
    try {
      setIsScanning(true);
      
      // Import BrowserMultiFormatReader
      const { BrowserMultiFormatReader } = await import('@zxing/library');
      
      // Use MultiFormatReader but validate results
      codeReader.current = new BrowserMultiFormatReader();
      
      // Request camera permissions first
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', // Try to use back camera
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      // Set the video stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      // Start scanning
      const result = await codeReader.current.decodeOnceFromVideoDevice(undefined, videoRef.current);
      
      if (result) {
        // Check if the barcode format is allowed (2D codes only)
        const format = result.getBarcodeFormat();
        const allowedFormats = ['DATA_MATRIX', 'QR_CODE', 'AZTEC', 'PDF_417'];
        
        if (!allowedFormats.includes(format.toString())) {
          setError(`❌ 1D barcode detected (${format}). Please scan a 2D code (Data Matrix, QR, Aztec, PDF417).`);
          setIsScanning(false);
          return;
        }
        
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
      
      // Import BrowserMultiFormatReader
      const { BrowserMultiFormatReader } = await import('@zxing/library');
      
      // Use MultiFormatReader but validate results
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
                // Check if the barcode format is allowed (2D codes only)
                const format = result.getBarcodeFormat();
                console.log('Detected barcode format:', format.toString());
                
                // Define 1D formats to reject
                const oneDFormats = [
                  'CODE_128', 'CODE_39', 'CODE_93', 'CODABAR', 'ITF', 'RSS_14', 'RSS_EXPANDED',
                  'UPC_A', 'UPC_E', 'EAN_13', 'EAN_8', 'UPC_EAN_EXTENSION'
                ];
                
                // Define 2D formats to allow
                const twoDFormats = ['DATA_MATRIX', 'QR_CODE', 'AZTEC', 'PDF_417'];
                
                const formatString = format.toString();
                
                if (oneDFormats.includes(formatString)) {
                  setError(`❌ 1D barcode detected (${formatString}). Please scan a 2D code (Data Matrix, QR, Aztec, PDF417).`);
                  // Continue scanning instead of stopping
                  setTimeout(scanLoop, 100);
                  return;
                } else if (!twoDFormats.includes(formatString)) {
                  setError(`❌ Unsupported barcode format (${formatString}). Please scan a 2D code (Data Matrix, QR, Aztec, PDF417).`);
                  // Continue scanning instead of stopping
                  setTimeout(scanLoop, 100);
                  return;
                }
                
                // Clear any previous errors if we got a valid 2D code
                setError('');
                
                const scannedData = result.getText();
                handleBarcodeResult(scannedData);
                
                // For single-item scanning, stop here
                // For multi-item scanning, shouldContinueScanning controls continuation
                if (!shouldContinueScanning) {
                  return;
                }
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
                // Check if the barcode format is allowed (2D codes only)
                const format = result.getBarcodeFormat();
                const allowedFormats = ['DATA_MATRIX', 'QR_CODE', 'AZTEC', 'PDF_417'];
                
                if (!allowedFormats.includes(format.toString())) {
                  setError(`❌ 1D barcode detected (${format}). Please scan a 2D code (Data Matrix, QR, Aztec, PDF417).`);
                  // Continue scanning instead of stopping
                  setTimeout(scanLoop, 100);
                  return;
                }
                
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
        const serialNumber = parsedData.serialNumber;
        const isItemsLevel = serialCollectionStep.currentLevel === 'item';
        
        // Check for duplicates against ALL existing serial numbers in the project
        const duplicates = validateDuplicateSerials(serialNumber);
        if (duplicates) {
          setError(`Duplicate serial number found! "${serialNumber}" is already used at: ${duplicates[0].path}`);
          return;
        }
        
        // Clear any previous errors
        setError('');
        
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
              setError(`Duplicate serial number! "${serialNumber}" was already scanned in this session.`);
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
          closeScanner();
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

  const renderStep1 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit}>
        
        <div className="business-document-section">
          <h3>Business Document Information</h3>
          <div className="business-entities-grid">
            
            {/* Sender Information */}
            <div className="business-entity-group">
              <h4>Sender Information</h4>
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
              <h4>Receiver Information</h4>
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
              <h4>Shipper Information</h4>
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
          <h3>Product Information (EPCClass)</h3>
          <div className="form-grid search-fda-wrapper">
            <div className="form-group fda-search-group">
              <label htmlFor="productNdc">Search FDA by Product NDC:</label>
              <div className="fda-search-container">
                <input
                  type="text"
                  id="productNdc"
                  value={configuration.productNdc}
                  onChange={(e) => setConfiguration({...configuration, productNdc: e.target.value})}
                  placeholder="e.g., 45802-466"
                />
                <button 
                  type="button" 
                  className="fda-search-button"
                  onClick={handleFdaSearch}
                  disabled={fdaModal.isLoading}
                >
                  {fdaModal.isLoading ? 'Searching...' : 'Search FDA'}
                </button>
              </div>
              <small className="form-hint">Enter 8-digit NDC (with hyphen) to search FDA and fill details below</small>
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
                placeholder="e.g., 85GM Wgt"
                required
              />
              <small className="form-hint">Package size and weight</small>
            </div>
            <div className="form-group">
              <label htmlFor="companyPrefix">GS1 Company Prefix:</label>
              <input
                type="text"
                id="companyPrefix"
                value={configuration.companyPrefix}
                onChange={(e) => setConfiguration({...configuration, companyPrefix: e.target.value})}
                placeholder="e.g., 0345802"
                required
              />
              <small className="form-hint">Manufacturer GS1 Company Prefix</small>
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
          <h3>Packaging Configuration {isPackagingConfigLocked && <span className="locked-indicator">(Locked - Serial Numbers Entered)</span>}</h3>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="numberOfSscc">Number of SSCCs:</label>
              <input
                type="number"
                id="numberOfSscc"
                min="1"
                max="20"
                value={configuration.numberOfSscc}
                onChange={(e) => setConfiguration({...configuration, numberOfSscc: e.target.value ? parseInt(e.target.value) : ''})}
                disabled={isPackagingConfigLocked}
                placeholder="e.g., 1"
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
                onChange={(e) => setConfiguration({...configuration, casesPerSscc: e.target.value ? parseInt(e.target.value) : ''})}
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
                checked={configuration.useInnerCases}
                onChange={(e) => setConfiguration({...configuration, useInnerCases: e.target.checked})}
                disabled={configuration.casesPerSscc === 0 || configuration.casesPerSscc === '' || isPackagingConfigLocked}
              />
              <span className="checkbox-text">
                <strong>Enable Inner Cases</strong>
                <small>{(configuration.casesPerSscc === 0 || configuration.casesPerSscc === '') ? 'Not available when Cases per SSCC = 0 or empty' : 'Add an intermediate packaging level between cases and items'}</small>
              </span>
            </label>
          </div>
          
          {configuration.casesPerSscc === 0 ? (
            <div className="packaging-config">
              <div className="form-group">
                <label htmlFor="itemsPerCase">Items per SSCC:</label>
                <input
                  type="number"
                  id="itemsPerCase"
                  min="1"
                  max="1000"
                  value={configuration.itemsPerCase}
                  onChange={(e) => setConfiguration({...configuration, itemsPerCase: e.target.value ? parseInt(e.target.value) : ''})}
                  disabled={isPackagingConfigLocked}
                  placeholder="e.g., 10"
                  required
                />
              </div>
              <div className="config-explanation">
                <p><strong>2-Level Hierarchy:</strong> SSCC → Items</p>
              </div>
            </div>
          ) : configuration.useInnerCases ? (
            <div className="packaging-config">
              <div className="grid grid-cols-2 gap-4 mb-0">
                <div className="form-group">
                  <label htmlFor="innerCasesPerCase">Inner Cases per Case:</label>
                  <input
                    type="number"
                    id="innerCasesPerCase"
                    min="1"
                    max="50"
                    value={configuration.innerCasesPerCase}
                    onChange={(e) => setConfiguration({...configuration, innerCasesPerCase: e.target.value ? parseInt(e.target.value) : ''})}
                    disabled={isPackagingConfigLocked}
                    placeholder="e.g., 2"
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
                    onChange={(e) => setConfiguration({...configuration, itemsPerInnerCase: e.target.value ? parseInt(e.target.value) : ''})}
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
                  min="1"
                  max="100"
                  value={configuration.itemsPerCase}
                  onChange={(e) => setConfiguration({...configuration, itemsPerCase: e.target.value ? parseInt(e.target.value) : ''})}
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
                  <strong>Cases:</strong> {calculateTotals().totalCases}
                </div>
                {configuration.useInnerCases && (
                  <>
                    <div className="hierarchy-arrow">↓</div>
                    <div className="hierarchy-level">
                      <strong>Inner Cases:</strong> {calculateTotals().totalInnerCases}
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

  const renderStep2 = () => {
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
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium"
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
                  <video ref={videoRef} className="scanner-video" autoPlay muted playsInline></video>
                  {isScanning && (
                    <div className="scanning-overlay">
                      <div className="scanning-frame"></div>
                      <p className="scanning-text">Scanning for 2D codes...</p>
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
                        <p className="preview-label">Scanned items (tap "Remove" to delete):</p>
                        <ul className="scanned-items-list">
                          {scannedItems.map((item, index) => (
                            <li key={index} className="scanned-item">
                              <div className="scanned-item-info">
                                <span className="item-number">{index + 1}.</span>
                                <span className="item-serial">{item}</span>
                              </div>
                              <button
                                onClick={() => removeScannedItem(index)}
                                className="remove-item-btn"
                                title={`Remove item ${index + 1}: ${item}`}
                              >
                                ✕ Remove
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="scanner-instructions">
                  <p><strong>2D Codes Only:</strong> Position Data Matrix, QR codes, Aztec, or PDF417 within the camera view</p>
                  <p className="format-restriction">❌ 1D barcodes (UPC, Code 128, etc.) are not supported</p>
                  {requiredItemCount > 1 && (
                    <p className="multi-scan-instruction">
                      <strong>Multi-scan mode:</strong> Scan {requiredItemCount} items to continue, or save partial progress
                    </p>
                  )}
                  {!isScanning && (
                    <p className="error-text">Camera not started. Please check permissions.</p>
                  )}
                </div>
              </div>
              <div className="scanner-footer">
                <button className="btn-secondary" onClick={closeScanner}>Cancel</button>
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
          </div>
          <div className="footer-wrapper"><img className="logo" src="https://rxerp.com/wp-content/uploads/2025/01/rxerp-logo-hero-tagline.svg"></img></div>
        </div>
      )}
    </AuthWrapper>
  );
}

export default App;