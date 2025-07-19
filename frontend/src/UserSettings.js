import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import axios from 'axios';

const UserSettings = ({ onClose }) => {
  const [userInfo, setUserInfo] = useState({
    firstName: '',
    lastName: '',
    email: '',
    companyName: '',
    streetAddress: '',
    city: '',
    state: '',
    postalCode: '',
    countryCode: ''
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { user, token, updateUser } = useAuth();

  // Locations state
  const [locations, setLocations] = useState([]);
  const [locationForm, setLocationForm] = useState({
    name: '',
    companyPrefix: '',
    gln: '',
    sgln: '',
    companyName: '',
    streetAddress: '',
    city: '',
    state: '',
    postalCode: '',
    countryCode: '',
    despatchAdviceNumber: ''
  });
  const [editingLocationId, setEditingLocationId] = useState(null);
  const [locationsLoading, setLocationsLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Location functions
  const loadLocations = async () => {
    try {
      setLocationsLoading(true);
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
      setLocationsLoading(false);
    }
  };

  const handleLocationFormChange = (e) => {
    setLocationForm({
      ...locationForm,
      [e.target.name]: e.target.value
    });
  };

  const resetLocationForm = () => {
    setLocationForm({
      name: '',
      companyPrefix: '',
      gln: '',
      sgln: '',
      companyName: '',
      streetAddress: '',
      city: '',
      state: '',
      postalCode: '',
      countryCode: '',
      despatchAdviceNumber: ''
    });
    setEditingLocationId(null);
  };

  const handleCreateLocation = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      
      if (!locationForm.name.trim()) {
        setError('Location name is required');
        return;
      }

      await axios.post(`${API}/locations`, locationForm, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setSuccess('Location created successfully');
      resetLocationForm();
      loadLocations();
    } catch (err) {
      console.error('Error creating location:', err);
      setError(err.response?.data?.detail || 'Failed to create location');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateLocation = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      
      if (!locationForm.name.trim()) {
        setError('Location name is required');
        return;
      }

      await axios.put(`${API}/locations/${editingLocationId}`, locationForm, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setSuccess('Location updated successfully');
      resetLocationForm();
      loadLocations();
    } catch (err) {
      console.error('Error updating location:', err);
      setError(err.response?.data?.detail || 'Failed to update location');
    } finally {
      setLoading(false);
    }
  };

  const handleEditLocation = (location) => {
    setLocationForm({
      name: location.name || '',
      companyPrefix: location.companyPrefix || '',
      gln: location.gln || '',
      sgln: location.sgln || '',
      companyName: location.companyName || '',
      streetAddress: location.streetAddress || '',
      city: location.city || '',
      state: location.state || '',
      postalCode: location.postalCode || '',
      countryCode: location.countryCode || '',
      despatchAdviceNumber: location.despatchAdviceNumber || ''
    });
    setEditingLocationId(location.id);
  };

  const handleDeleteLocation = async (locationId) => {
    if (!window.confirm('Are you sure you want to delete this location?')) {
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      await axios.delete(`${API}/locations/${locationId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setSuccess('Location deleted successfully');
      loadLocations();
    } catch (err) {
      console.error('Error deleting location:', err);
      setError(err.response?.data?.detail || 'Failed to delete location');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      setUserInfo({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        email: user.email || '',
        companyName: user.company_name || '',
        streetAddress: user.street_address || '',
        city: user.city || '',
        state: user.state || '',
        postalCode: user.postal_code || '',
        countryCode: user.country_code || ''
      });
    }
    
    // Load locations when component mounts or tab changes to locations
    if (activeTab === 'locations') {
      loadLocations();
    }
  }, [user, activeTab]);

  const handleUserInfoChange = (e) => {
    setUserInfo({
      ...userInfo,
      [e.target.name]: e.target.value
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await axios.put(`${API}/auth/profile`, userInfo, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess('Profile updated successfully!');
      // Update the user context with new data
      updateUser(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (passwordData.newPassword !== passwordData.confirmNewPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setError('New password must be at least 6 characters long');
      return;
    }

    setLoading(true);

    try {
      await axios.put(`${API}/auth/password`, {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess('Password updated successfully!');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: ''
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">User Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('profile')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'profile'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Profile Information
            </button>
            <button
              onClick={() => setActiveTab('password')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'password'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Change Password
            </button>
            <button
              onClick={() => setActiveTab('locations')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'locations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Locations
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Success/Error Messages */}
          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="text-green-800">{success}</div>
            </div>
          )}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="text-red-800">{error}</div>
            </div>
          )}

          {/* Profile Information Tab */}
          {activeTab === 'profile' && (
            <form onSubmit={handleUpdateProfile}>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        name="firstName"
                        value={userInfo.firstName}
                        onChange={handleUserInfoChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        name="lastName"
                        value={userInfo.lastName}
                        onChange={handleUserInfoChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={userInfo.email}
                      onChange={handleUserInfoChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Company Information</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Name
                    </label>
                    <input
                      type="text"
                      name="companyName"
                      value={userInfo.companyName}
                      onChange={handleUserInfoChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Street Address
                    </label>
                    <input
                      type="text"
                      name="streetAddress"
                      value={userInfo.streetAddress}
                      onChange={handleUserInfoChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        City
                      </label>
                      <input
                        type="text"
                        name="city"
                        value={userInfo.city}
                        onChange={handleUserInfoChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        State
                      </label>
                      <input
                        type="text"
                        name="state"
                        value={userInfo.state}
                        onChange={handleUserInfoChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Postal Code
                      </label>
                      <input
                        type="text"
                        name="postalCode"
                        value={userInfo.postalCode}
                        onChange={handleUserInfoChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Country Code
                    </label>
                    <input
                      type="text"
                      name="countryCode"
                      value={userInfo.countryCode}
                      onChange={handleUserInfoChange}
                      placeholder="e.g., US, CA, UK"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-8 flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}

          {/* Change Password Tab */}
          {activeTab === 'password' && (
            <form onSubmit={handleUpdatePassword}>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Current Password
                      </label>
                      <input
                        type="password"
                        name="currentPassword"
                        value={passwordData.currentPassword}
                        onChange={handlePasswordChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        New Password
                      </label>
                      <input
                        type="password"
                        name="newPassword"
                        value={passwordData.newPassword}
                        onChange={handlePasswordChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                      <p className="mt-1 text-sm text-gray-500">
                        Password must be at least 6 characters long
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        name="confirmNewPassword"
                        value={passwordData.confirmNewPassword}
                        onChange={handlePasswordChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserSettings;