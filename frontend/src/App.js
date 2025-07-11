import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [configuration, setConfiguration] = useState({
    itemsPerCase: 10,
    casesPerSscc: 5,
    numberOfSscc: 2,
    companyPrefix: '1234567',
    itemProductCode: '000000',
    caseProductCode: '111111',
    ssccIndicatorDigit: '0',
    caseIndicatorDigit: '0',
    itemIndicatorDigit: '0'
  });
  const [configurationId, setConfigurationId] = useState('');
  const [ssccSerials, setSsccSerials] = useState([]);
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
        cases_per_sscc: configuration.casesPerSscc,
        number_of_sscc: configuration.numberOfSscc,
        company_prefix: configuration.companyPrefix,
        item_product_code: configuration.itemProductCode,
        case_product_code: configuration.caseProductCode,
        sscc_indicator_digit: configuration.ssccIndicatorDigit,
        case_indicator_digit: configuration.caseIndicatorDigit,
        item_indicator_digit: configuration.itemIndicatorDigit
      });
      
      setConfigurationId(response.data.id);
      
      // Calculate totals
      const totalCases = configuration.casesPerSscc * configuration.numberOfSscc;
      const totalItems = configuration.itemsPerCase * totalCases;
      
      // Initialize serial number arrays
      setSsccSerials(new Array(configuration.numberOfSscc).fill(''));
      setCaseSerials(new Array(totalCases).fill(''));
      setItemSerials(new Array(totalItems).fill(''));
      
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
    if (ssccSerials.some(serial => !serial.trim()) || 
        caseSerials.some(serial => !serial.trim()) || 
        itemSerials.some(serial => !serial.trim())) {
      setError('All serial numbers must be filled');
      setIsLoading(false);
      return;
    }
    
    try {
      await axios.post(`${API}/serial-numbers`, {
        configuration_id: configurationId,
        sscc_serial_numbers: ssccSerials,
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
      companyPrefix: '1234567',
      itemProductCode: '000000',
      caseProductCode: '111111',
      ssccIndicatorDigit: '0',
      caseIndicatorDigit: '0',
      itemIndicatorDigit: '0'
    });
    setConfigurationId('');
    setSsccSerials([]);
    setCaseSerials([]);
    setItemSerials([]);
    setError('');
    setSuccess('');
  };

  const renderStep1 = () => (
    <div className="step-container">
      <h2 className="step-title">Step 1: Configuration</h2>
      <form onSubmit={handleConfigurationSubmit} className="config-form">
        <div className="form-grid">
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
              <small className="form-hint">Product code for individual items</small>
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
              <strong>Cases:</strong> {configuration.casesPerSscc * configuration.numberOfSscc} total
            </div>
            <div className="hierarchy-arrow">↓</div>
            <div className="hierarchy-level">
              <strong>Items:</strong> {configuration.itemsPerCase * configuration.casesPerSscc * configuration.numberOfSscc} total
            </div>
          </div>
        </div>
        
        <div className="summary">
          <h4>GS1 Identifier Examples</h4>
          <p><strong>SSCC:</strong> urn:epc:id:sscc:{configuration.companyPrefix}.{configuration.ssccIndicatorDigit}[sscc_serial]</p>
          <p><strong>Case SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.caseIndicatorDigit}{configuration.caseProductCode}.[case_serial]</p>
          <p><strong>Item SGTIN:</strong> urn:epc:id:sgtin:{configuration.companyPrefix}.{configuration.itemIndicatorDigit}{configuration.itemProductCode}.[item_serial]</p>
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
            <li>Company Prefix: {configuration.companyPrefix}</li>
            <li>Product Code: {configuration.productCode}</li>
            <li>Case Indicator: {configuration.caseIndicatorDigit}</li>
            <li>Item Indicator: {configuration.itemIndicatorDigit}</li>
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