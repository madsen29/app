import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [configuration, setConfiguration] = useState({
    itemsPerCase: 10,
    numberOfCases: 5,
    companyPrefix: '1234567',
    productCode: '000000',
    caseIndicatorDigit: '0',
    itemIndicatorDigit: '0'
  });
  const [configurationId, setConfigurationId] = useState('');
  const [caseSerials, setCaseSerials] = useState([]);
  const [itemSerials, setItemSerials] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleConfigurationSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/configuration`, {
        items_per_case: configuration.itemsPerCase,
        number_of_cases: configuration.numberOfCases,
        company_prefix: configuration.companyPrefix,
        product_code: configuration.productCode,
        case_indicator_digit: configuration.caseIndicatorDigit,
        item_indicator_digit: configuration.itemIndicatorDigit
      });
      
      setConfigurationId(response.data.id);
      
      // Initialize serial number arrays
      setCaseSerials(new Array(configuration.numberOfCases).fill(''));
      setItemSerials(new Array(configuration.itemsPerCase * configuration.numberOfCases).fill(''));
      
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
    
    // Validate all serial numbers are filled
    if (caseSerials.some(serial => !serial.trim()) || itemSerials.some(serial => !serial.trim())) {
      setError('All serial numbers must be filled');
      setIsLoading(false);
      return;
    }
    
    try {
      await axios.post(`${API}/serial-numbers`, {
        configuration_id: configurationId,
        case_serial_numbers: caseSerials,
        item_serial_numbers: itemSerials
      });
      
      setCurrentStep(3);
      setSuccess('Serial numbers saved successfully!');
    } catch (err) {
      setError('Failed to save serial numbers');
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
        company_prefix: "1234567",
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
    setConfiguration({ itemsPerCase: 10, numberOfCases: 5 });
    setConfigurationId('');
    setCaseSerials([]);
    setItemSerials([]);
    setError('');
    setSuccess('');
  };

  const renderStep1 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit} className="config-form">
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
        <div className="form-group">
          <label htmlFor="numberOfCases">Number of Cases:</label>
          <input
            type="number"
            id="numberOfCases"
            min="1"
            max="50"
            value={configuration.numberOfCases}
            onChange={(e) => setConfiguration({...configuration, numberOfCases: parseInt(e.target.value)})}
            required
          />
        </div>
        <div className="summary">
          <p>Total Items: {configuration.itemsPerCase * configuration.numberOfCases}</p>
        </div>
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );

  const renderStep2 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 2: Serial Numbers</h2>
      <form onSubmit={handleSerialNumbersSubmit} className="serial-form">
        
        <div className="serial-section">
          <h3>Case Serial Numbers</h3>
          <div className="serial-grid">
            {caseSerials.map((serial, index) => (
              <div key={index} className="serial-input-group">
                <label>Case {index + 1}:</label>
                <input
                  type="text"
                  value={serial}
                  onChange={(e) => {
                    const newSerials = [...caseSerials];
                    newSerials[index] = e.target.value;
                    setCaseSerials(newSerials);
                  }}
                  placeholder={`Case ${index + 1} serial number`}
                  required
                />
              </div>
            ))}
          </div>
        </div>

        <div className="serial-section">
          <h3>Item Serial Numbers</h3>
          <div className="serial-grid">
            {itemSerials.map((serial, index) => {
              const caseNumber = Math.floor(index / configuration.itemsPerCase) + 1;
              const itemNumber = (index % configuration.itemsPerCase) + 1;
              return (
                <div key={index} className="serial-input-group">
                  <label>Case {caseNumber} - Item {itemNumber}:</label>
                  <input
                    type="text"
                    value={serial}
                    onChange={(e) => {
                      const newSerials = [...itemSerials];
                      newSerials[index] = e.target.value;
                      setItemSerials(newSerials);
                    }}
                    placeholder={`Item ${index + 1} serial number`}
                    required
                  />
                </div>
              );
            })}
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

  const renderStep3 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 3: Generate EPCIS File</h2>
      <div className="summary-section">
        <h3>Configuration Summary</h3>
        <div className="summary-grid">
          <div className="summary-item">
            <strong>Items per Case:</strong> {configuration.itemsPerCase}
          </div>
          <div className="summary-item">
            <strong>Number of Cases:</strong> {configuration.numberOfCases}
          </div>
          <div className="summary-item">
            <strong>Total Items:</strong> {configuration.itemsPerCase * configuration.numberOfCases}
          </div>
        </div>
        
        <div className="epcis-info">
          <h4>EPCIS File Details</h4>
          <p>The generated file will contain GS1 compliant EPCIS XML with aggregation events for pharmaceutical serialization.</p>
          <ul>
            <li>Company Prefix: 1234567</li>
            <li>Format: EPCIS 2.0 Standard</li>
            <li>Event Type: Aggregation Events</li>
            <li>Business Step: Packing</li>
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

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Rx EPCIS Serial Number Aggregation</h1>
          <p>Generate GS1 compliant EPCIS files for pharmaceutical serialization</p>
        </header>

        <div className="progress-bar">
          <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>1</div>
          <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>2</div>
          <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>3</div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

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