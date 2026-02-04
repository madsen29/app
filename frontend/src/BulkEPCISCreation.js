import React, { useState, useRef } from 'react';
import { FiUpload, FiFile, FiX, FiDownload, FiAlertCircle, FiAlertTriangle, FiCheckCircle, FiArrowLeft, FiPackage } from 'react-icons/fi';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BulkEPCISCreation = ({ onBack }) => {
  // File state
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef(null);
  
  // Form state
  const [shippingSSCC, setShippingSSCC] = useState('');
  const [senderLocation, setSenderLocation] = useState({
    name: '',
    streetAddressOne: '',
    city: '',
    state: '',
    postalCode: '',
    countryCode: '',
    sgln: ''
  });
  const [receiverLocation, setReceiverLocation] = useState({
    name: '',
    streetAddressOne: '',
    city: '',
    state: '',
    postalCode: '',
    countryCode: '',
    sgln: ''
  });
  
  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  
  // Handle file selection
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setFileError('');
    
    if (!file) {
      setSelectedFile(null);
      return;
    }
    
    if (!file.name.endsWith('.json')) {
      setFileError('Only .json files are accepted');
      setSelectedFile(null);
      return;
    }
    
    // Validate JSON syntax
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        JSON.parse(event.target.result);
        setSelectedFile(file);
      } catch (err) {
        setFileError(`Invalid JSON syntax: ${err.message}`);
        setSelectedFile(null);
      }
    };
    reader.readAsText(file);
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    
    // Validation
    if (!selectedFile) {
      setError({ message: 'Please select a JSON file' });
      return;
    }
    
    if (!shippingSSCC.trim()) {
      setError({ message: 'Shipping SSCC is required' });
      return;
    }
    
    if (!senderLocation.name || !senderLocation.city || !senderLocation.countryCode || !senderLocation.sgln) {
      setError({ message: 'Sender location requires name, city, country code, and SGLN' });
      return;
    }
    
    if (!receiverLocation.name || !receiverLocation.city || !receiverLocation.countryCode || !receiverLocation.sgln) {
      setError({ message: 'Receiver location requires name, city, country code, and SGLN' });
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('shipping_sscc', shippingSSCC);
      
      // Sender location
      formData.append('sender_name', senderLocation.name);
      formData.append('sender_street_address', senderLocation.streetAddressOne);
      formData.append('sender_city', senderLocation.city);
      formData.append('sender_state', senderLocation.state);
      formData.append('sender_postal_code', senderLocation.postalCode);
      formData.append('sender_country_code', senderLocation.countryCode);
      formData.append('sender_sgln', senderLocation.sgln);
      
      // Receiver location
      formData.append('receiver_name', receiverLocation.name);
      formData.append('receiver_street_address', receiverLocation.streetAddressOne);
      formData.append('receiver_city', receiverLocation.city);
      formData.append('receiver_state', receiverLocation.state);
      formData.append('receiver_postal_code', receiverLocation.postalCode);
      formData.append('receiver_country_code', receiverLocation.countryCode);
      formData.append('receiver_sgln', receiverLocation.sgln);
      
      const response = await axios.post(`${API}/epcis/bulk-create`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setResult(response.data);
    } catch (err) {
      console.error('Bulk EPCIS creation error:', err);
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'object') {
          setError({
            message: detail.message || 'Validation failed',
            errors: detail.errors || [],
            warnings: detail.warnings || []
          });
        } else {
          setError({ message: detail });
        }
      } else {
        setError({ message: err.message || 'An error occurred' });
      }
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Handle XML download
  const handleDownload = () => {
    if (!result?.xmlContent) return;
    
    const blob = new Blob([result.xmlContent], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.summary.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // Reset form
  const handleReset = () => {
    setSelectedFile(null);
    setFileError('');
    setShippingSSCC('');
    setSenderLocation({
      name: '',
      streetAddressOne: '',
      city: '',
      state: '',
      postalCode: '',
      countryCode: '',
      sgln: ''
    });
    setReceiverLocation({
      name: '',
      streetAddressOne: '',
      city: '',
      state: '',
      postalCode: '',
      countryCode: '',
      sgln: ''
    });
    setError(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="flex items-center text-slate-400 hover:text-white transition-colors"
                data-testid="back-to-dashboard-btn"
              >
                <FiArrowLeft className="mr-2" />
                Back
              </button>
              <div className="flex items-center space-x-3">
                <FiPackage className="text-blue-400 text-2xl" />
                <h1 className="text-xl font-semibold">Bulk EPCIS Creation</h1>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Result Summary */}
        {result && (
          <div className="mb-8 bg-slate-800 rounded-lg border border-green-500/50 p-6" data-testid="result-summary">
            <div className="flex items-center mb-4">
              <FiCheckCircle className="text-green-500 text-2xl mr-3" />
              <h2 className="text-xl font-semibold text-green-400">EPCIS Generated Successfully</h2>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">Records Processed</div>
                <div className="text-2xl font-bold text-white">{result.summary.totalRecordsProcessed}</div>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">SGTINs Parsed</div>
                <div className="text-2xl font-bold text-green-400">{result.summary.sgtinsSuccessfullyParsed}</div>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">Commissioning Events</div>
                <div className="text-2xl font-bold text-blue-400">{result.summary.commissioningEventsCreated}</div>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">Aggregation Events</div>
                <div className="text-2xl font-bold text-purple-400">{result.summary.aggregationEventsCreated}</div>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">Root EPCs Aggregated</div>
                <div className="text-2xl font-bold text-white">{result.summary.rootEpcsAggregated}</div>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <div className="text-sm text-slate-400">Max Hierarchy Depth</div>
                <div className="text-2xl font-bold text-white">{result.summary.maxHierarchyDepth}</div>
              </div>
            </div>
            
            <div className="text-sm text-slate-400 mb-4">
              <span className="font-medium">Shipment:</span> {result.summary.senderSgln} → {result.summary.receiverSgln}
            </div>
            
            {result.summary.validationWarnings.length > 0 && (
              <div className="mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <FiAlertTriangle className="text-yellow-500 mr-2" />
                  <span className="text-yellow-400 font-medium">Warnings</span>
                </div>
                <ul className="text-sm text-yellow-200 space-y-1 max-h-32 overflow-y-auto">
                  {result.summary.validationWarnings.map((warning, idx) => (
                    <li key={idx}>• {warning}</li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="flex space-x-4">
              <button
                onClick={handleDownload}
                className="flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors"
                data-testid="download-epcis-btn"
              >
                <FiDownload className="mr-2" />
                Download EPCIS XML
              </button>
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition-colors"
                data-testid="create-another-btn"
              >
                Create Another
              </button>
            </div>
          </div>
        )}
        
        {/* Error Display */}
        {error && (
          <div className="mb-8 bg-red-500/10 border border-red-500/50 rounded-lg p-6" data-testid="error-display">
            <div className="flex items-center mb-2">
              <FiAlertCircle className="text-red-500 text-xl mr-2" />
              <span className="text-red-400 font-medium">{error.message}</span>
            </div>
            {error.errors && error.errors.length > 0 && (
              <ul className="text-sm text-red-200 space-y-1 mt-2">
                {error.errors.map((err, idx) => (
                  <li key={idx}>• {err}</li>
                ))}
              </ul>
            )}
            {error.warnings && error.warnings.length > 0 && (
              <div className="mt-4 pt-4 border-t border-red-500/30">
                <div className="text-yellow-400 text-sm font-medium mb-1">Warnings:</div>
                <ul className="text-sm text-yellow-200 space-y-1">
                  {error.warnings.map((warn, idx) => (
                    <li key={idx}>• {warn}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {/* Form */}
        {!result && (
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* File Upload Section */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <FiUpload className="mr-2 text-blue-400" />
                JSON File Upload
              </h2>
              
              <div
                className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  selectedFile
                    ? 'border-green-500/50 bg-green-500/5'
                    : fileError
                    ? 'border-red-500/50 bg-red-500/5'
                    : 'border-slate-600 hover:border-slate-500'
                }`}
              >
                {selectedFile ? (
                  <div className="flex items-center justify-center space-x-4">
                    <FiFile className="text-green-400 text-3xl" />
                    <div className="text-left">
                      <div className="text-white font-medium">{selectedFile.name}</div>
                      <div className="text-sm text-slate-400">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFile(null);
                        if (fileInputRef.current) fileInputRef.current.value = '';
                      }}
                      className="p-2 hover:bg-slate-700 rounded-full transition-colors"
                    >
                      <FiX className="text-slate-400 hover:text-red-400" />
                    </button>
                  </div>
                ) : (
                  <div>
                    <FiUpload className="mx-auto text-4xl text-slate-500 mb-4" />
                    <p className="text-slate-400 mb-2">
                      Drag and drop your JSON file here, or click to browse
                    </p>
                    <p className="text-sm text-slate-500">Only .json files are accepted</p>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileSelect}
                  className={selectedFile ? 'hidden' : 'absolute inset-0 w-full h-full opacity-0 cursor-pointer'}
                  data-testid="json-file-input"
                />
              </div>
              
              {fileError && (
                <div className="mt-2 text-red-400 text-sm flex items-center">
                  <FiAlertCircle className="mr-1" />
                  {fileError}
                </div>
              )}
            </div>
            
            {/* Shipping SSCC */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4">Shipping SSCC</h2>
              <input
                type="text"
                value={shippingSSCC}
                onChange={(e) => setShippingSSCC(e.target.value)}
                placeholder="18-digit SSCC (e.g., 003030781729685000)"
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                data-testid="shipping-sscc-input"
              />
              <p className="mt-2 text-sm text-slate-400">
                This SSCC will be used as the parent for the mass aggregation and in the final shipping event.
              </p>
            </div>
            
            {/* Sender Location */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4">Sender Location</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Name *</label>
                  <input
                    type="text"
                    value={senderLocation.name}
                    onChange={(e) => setSenderLocation({ ...senderLocation, name: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-name-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">SGLN *</label>
                  <input
                    type="text"
                    value={senderLocation.sgln}
                    onChange={(e) => setSenderLocation({ ...senderLocation, sgln: e.target.value })}
                    placeholder="e.g., 0303078172968.00000.0"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-sgln-input"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-400 mb-1">Street Address</label>
                  <input
                    type="text"
                    value={senderLocation.streetAddressOne}
                    onChange={(e) => setSenderLocation({ ...senderLocation, streetAddressOne: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-street-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">City *</label>
                  <input
                    type="text"
                    value={senderLocation.city}
                    onChange={(e) => setSenderLocation({ ...senderLocation, city: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-city-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">State</label>
                  <input
                    type="text"
                    value={senderLocation.state}
                    onChange={(e) => setSenderLocation({ ...senderLocation, state: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-state-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Postal Code</label>
                  <input
                    type="text"
                    value={senderLocation.postalCode}
                    onChange={(e) => setSenderLocation({ ...senderLocation, postalCode: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-postal-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Country Code *</label>
                  <input
                    type="text"
                    value={senderLocation.countryCode}
                    onChange={(e) => setSenderLocation({ ...senderLocation, countryCode: e.target.value })}
                    placeholder="e.g., US"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="sender-country-input"
                  />
                </div>
              </div>
            </div>
            
            {/* Receiver Location */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4">Receiver Location</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Name *</label>
                  <input
                    type="text"
                    value={receiverLocation.name}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, name: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-name-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">SGLN *</label>
                  <input
                    type="text"
                    value={receiverLocation.sgln}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, sgln: e.target.value })}
                    placeholder="e.g., 0860000318304.00000.0"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-sgln-input"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm text-slate-400 mb-1">Street Address</label>
                  <input
                    type="text"
                    value={receiverLocation.streetAddressOne}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, streetAddressOne: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-street-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">City *</label>
                  <input
                    type="text"
                    value={receiverLocation.city}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, city: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-city-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">State</label>
                  <input
                    type="text"
                    value={receiverLocation.state}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, state: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-state-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Postal Code</label>
                  <input
                    type="text"
                    value={receiverLocation.postalCode}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, postalCode: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-postal-input"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Country Code *</label>
                  <input
                    type="text"
                    value={receiverLocation.countryCode}
                    onChange={(e) => setReceiverLocation({ ...receiverLocation, countryCode: e.target.value })}
                    placeholder="e.g., US"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="receiver-country-input"
                  />
                </div>
              </div>
            </div>
            
            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isProcessing || !selectedFile}
                className={`px-8 py-3 rounded-lg font-medium transition-colors flex items-center ${
                  isProcessing || !selectedFile
                    ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
                data-testid="generate-epcis-btn"
              >
                {isProcessing ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    <FiPackage className="mr-2" />
                    Generate EPCIS
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
};

export default BulkEPCISCreation;
