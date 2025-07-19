import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const LocationSelector = ({ isOpen, onClose, onSelectLocation, targetSection }) => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    if (isOpen) {
      loadLocations();
    }
  }, [isOpen]);

  const loadLocations = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API}/locations`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setLocations(response.data.locations || []);
    } catch (err) {
      console.error('Error loading locations:', err);
      setError('Failed to load locations');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLocation = (location) => {
    // Map location data to configuration fields based on target section
    const locationData = {
      [`${targetSection}CompanyPrefix`]: location.companyPrefix || '',
      [`${targetSection}Gln`]: location.gln || '',
      [`${targetSection}Sgln`]: location.sgln || '',
      [`${targetSection}Name`]: location.companyName || '',
      [`${targetSection}StreetAddress`]: location.streetAddress || '',
      [`${targetSection}City`]: location.city || '',
      [`${targetSection}State`]: location.state || '',
      [`${targetSection}PostalCode`]: location.postalCode || '',
      [`${targetSection}CountryCode`]: location.countryCode || '',
    };

    // Add despatch advice number only for sender
    if (targetSection === 'sender') {
      locationData[`${targetSection}DespatchAdviceNumber`] = location.despatchAdviceNumber || '';
    }

    onSelectLocation(locationData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              Select Location for {targetSection.charAt(0).toUpperCase() + targetSection.slice(1)}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="text-red-800">{error}</div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">
              <div className="text-gray-600">Loading locations...</div>
            </div>
          ) : locations.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-500 mb-4">No locations available</div>
              <div className="text-sm text-gray-400">
                Go to Settings → Locations to create your first location.
              </div>
            </div>
          ) : (
            <div className="grid gap-4">
              {locations.map(location => (
                <div 
                  key={location.id} 
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-colors"
                  onClick={() => handleSelectLocation(location)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">{location.name}</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 text-sm text-gray-600">
                        {location.companyName && (
                          <div><span className="font-medium">Company:</span> {location.companyName}</div>
                        )}
                        {location.gln && (
                          <div><span className="font-medium">GLN:</span> {location.gln}</div>
                        )}
                        {location.sgln && (
                          <div><span className="font-medium">SGLN:</span> {location.sgln}</div>
                        )}
                        {location.streetAddress && (
                          <div><span className="font-medium">Address:</span> {location.streetAddress}</div>
                        )}
                        {(location.city || location.state) && (
                          <div>
                            <span className="font-medium">Location:</span> {[location.city, location.state].filter(Boolean).join(', ')}
                          </div>
                        )}
                        {location.countryCode && (
                          <div><span className="font-medium">Country:</span> {location.countryCode}</div>
                        )}
                        {location.companyPrefix && (
                          <div><span className="font-medium">Company Prefix:</span> {location.companyPrefix}</div>
                        )}
                        {location.despatchAdviceNumber && targetSection === 'sender' && (
                          <div><span className="font-medium">Despatch Advice:</span> {location.despatchAdviceNumber}</div>
                        )}
                      </div>
                    </div>
                    <div className="ml-4">
                      <button className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        Select
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LocationSelector;