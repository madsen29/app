import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import UserSettings from './UserSettings';
import { FiEdit2, FiTrash2, FiPlus, FiSettings, FiLogOut } from 'react-icons/fi';

const ProjectDashboard = ({ onSelectProject, onCreateProject, onLogout }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('updated_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUserSettings, setShowUserSettings] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [projectsPerPage] = useState(10);
  
  // Batch delete state
  const [selectedProjects, setSelectedProjects] = useState(new Set());
  const [isAllSelected, setIsAllSelected] = useState(false);
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false);
  
  // Rename project state
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameProject, setRenameProject] = useState(null);
  const [renameProjectName, setRenameProjectName] = useState('');
  
  // Avatar dropdown state
  const [showAvatarDropdown, setShowAvatarDropdown] = useState(false);
  const [renameLoading, setRenameLoading] = useState(false);
  
  const { token, user } = useAuth();

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  // Helper function to calculate totals for a project
  const calculateProjectTotals = (config) => {
    if (!config) return { totalCases: 0, totalInnerCases: 0, totalItems: 0 };
    
    const numberOfSscc = config.numberOfSscc || 0;
    const casesPerSscc = config.casesPerSscc || 0;
    const itemsPerCase = config.itemsPerCase || 0;
    const useInnerCases = config.useInnerCases || false;
    const innerCasesPerCase = config.innerCasesPerCase || 0;
    const itemsPerInnerCase = config.itemsPerInnerCase || 0;
    
    let totalCases = 0;
    let totalInnerCases = 0;
    let totalItems = 0;
    
    if (casesPerSscc === 0) {
      // Direct SSCC → Items
      totalItems = numberOfSscc * itemsPerCase;
    } else if (useInnerCases) {
      // SSCC → Cases → Inner Cases → Items
      totalCases = numberOfSscc * casesPerSscc;
      totalInnerCases = totalCases * innerCasesPerCase;
      totalItems = totalInnerCases * itemsPerInnerCase;
    } else {
      // SSCC → Cases → Items
      totalCases = numberOfSscc * casesPerSscc;
      totalItems = totalCases * itemsPerCase;
    }
    
    return { totalCases, totalInnerCases, totalItems };
  };

  // Helper function to check if packaging configuration is set and locked
  const isPackagingConfigSetAndLocked = (project) => {
    if (!project.configuration) return false;
    
    // Check if packaging configuration is set (not empty)
    const packagingSet = (
      project.configuration.numberOfSscc !== '' && 
      project.configuration.numberOfSscc !== null &&
      project.configuration.casesPerSscc !== '' && 
      project.configuration.casesPerSscc !== null &&
      project.configuration.itemsPerCase !== '' && 
      project.configuration.itemsPerCase !== null
    );
    
    // Check if project has serial numbers (indicating it's locked)
    const hasSerialNumbers = project.serial_numbers && project.serial_numbers.length > 0;
    
    return packagingSet && hasSerialNumbers;
  };

  // Pagination helper functions
  const getTotalPages = () => Math.ceil(projects.length / projectsPerPage);
  const getCurrentPageProjects = () => {
    const startIndex = (currentPage - 1) * projectsPerPage;
    const endIndex = startIndex + projectsPerPage;
    return sortedProjects.slice(startIndex, endIndex);
  };

  // Batch delete helper functions
  const handleSelectProject = (projectId) => {
    const newSelected = new Set(selectedProjects);
    if (newSelected.has(projectId)) {
      newSelected.delete(projectId);
    } else {
      newSelected.add(projectId);
    }
    setSelectedProjects(newSelected);
    setIsAllSelected(newSelected.size === getCurrentPageProjects().length);
  };

  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedProjects(new Set());
      setIsAllSelected(false);
    } else {
      const currentPageProjectIds = getCurrentPageProjects().map(p => p.id);
      setSelectedProjects(new Set(currentPageProjectIds));
      setIsAllSelected(true);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedProjects.size === 0) return;
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedProjects.size} project${selectedProjects.size > 1 ? 's' : ''}? This action cannot be undone.`
    );
    
    if (!confirmDelete) return;
    
    setBatchDeleteLoading(true);
    setError('');
    
    try {
      const deletePromises = Array.from(selectedProjects).map(projectId =>
        axios.delete(`${API}/projects/${projectId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      );
      
      await Promise.all(deletePromises);
      
      // Remove deleted projects from state
      setProjects(projects.filter(p => !selectedProjects.has(p.id)));
      setSelectedProjects(new Set());
      setIsAllSelected(false);
      
      // Adjust current page if necessary
      const newTotalPages = Math.ceil((projects.length - selectedProjects.size) / projectsPerPage);
      if (currentPage > newTotalPages && newTotalPages > 0) {
        setCurrentPage(newTotalPages);
      }
      
    } catch (err) {
      setError('Failed to delete some projects. Please try again.');
      console.error('Error deleting projects:', err);
    } finally {
      setBatchDeleteLoading(false);
    }
  };

  // Rename project functions
  const handleRenameClick = (project) => {
    setRenameProject(project);
    setRenameProjectName(project.name);
    setShowRenameModal(true);
  };

  const handleRenameProject = async () => {
    if (!renameProjectName.trim() || !renameProject) return;
    
    setRenameLoading(true);
    setError('');
    
    try {
      const response = await axios.put(`${API}/projects/${renameProject.id}`, {
        name: renameProjectName.trim()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.status === 200) {
        // Update the project in the projects list
        setProjects(projects.map(p => 
          p.id === renameProject.id 
            ? { ...p, name: renameProjectName.trim() }
            : p
        ));
        
        setShowRenameModal(false);
        setRenameProject(null);
        setRenameProjectName('');
      }
    } catch (err) {
      setError('Failed to rename project. Please try again.');
      console.error('Error renaming project:', err);
    } finally {
      setRenameLoading(false);
    }
  };

  const handleCancelRename = () => {
    setShowRenameModal(false);
    setRenameProject(null);
    setRenameProjectName('');
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (err) {
      setError('Failed to fetch projects');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    setCreateLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/projects`, {
        name: newProjectName.trim()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update projects list first so generateSuggestedName can see the new project
      const updatedProjects = [response.data, ...projects];
      setProjects(updatedProjects);
      
      // Clear the form and close modal
      setNewProjectName('');
      setShowCreateModal(false);
      
      // Automatically select the new project
      if (onSelectProject) {
        onSelectProject(response.data);
      }
    } catch (err) {
      setError('Failed to create project');
      console.error('Error creating project:', err);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;

    try {
      await axios.delete(`${API}/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (err) {
      setError('Failed to delete project');
      console.error('Error deleting project:', err);
    }
  };

  const handleDownloadEPCIS = async (projectId) => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}/download-epcis`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'epcis-file.xml';
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
    } catch (err) {
      setError('Failed to download EPCIS file');
      console.error('Error downloading EPCIS:', err);
    }
  };

  const sortedProjects = [...projects].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];
    
    // Handle date sorting
    if (sortBy === 'created_at' || sortBy === 'updated_at') {
      aValue = new Date(aValue);
      bValue = new Date(bValue);
    }
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const generateSuggestedName = () => {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
    
    // Base name pattern for today
    const baseNamePattern = `EPCIS Project - ${dateStr}`;
    
    // Find all projects created today with the same base pattern
    const todayProjects = projects.filter(project => {
      return project.name.startsWith(baseNamePattern);
    });
    
    // Extract numbers from existing project names
    const existingNumbers = todayProjects.map(project => {
      const match = project.name.match(/\((\d+)\)$/);
      return match ? parseInt(match[1]) : 0;
    }).filter(num => num > 0);
    
    // Find the next available number
    const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;
    
    return `${baseNamePattern} (${nextNumber})`;
  };

  const handleCreateProjectClick = () => {
    // Generate a fresh suggested name each time the modal opens
    setNewProjectName(generateSuggestedName());
    setShowCreateModal(true);
  };

  // Avatar dropdown functions
  const getAvatarColor = (name) => {
    if (!name) return '#3b82f6';
    const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#f97316', '#06b6d4', '#84cc16'];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name.charAt(0).toUpperCase();
  };

  const handleAvatarClick = () => {
    setShowAvatarDropdown(!showAvatarDropdown);
  };

  const handleClickOutside = (event) => {
    if (showAvatarDropdown && !event.target.closest('.avatar-dropdown')) {
      setShowAvatarDropdown(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showAvatarDropdown]);

  const AvatarDropdown = () => (
    <div className="avatar-dropdown">
      <button
        onClick={handleAvatarClick}
        className="avatar-button"
        style={{ backgroundColor: getAvatarColor(user?.first_name || user?.email) }}
      >
        {getInitials(user?.first_name || user?.email)}
      </button>
      {showAvatarDropdown && (
        <div className="avatar-dropdown-menu">
          <button
            onClick={() => {
              setShowUserSettings(true);
              setShowAvatarDropdown(false);
            }}
            className="avatar-dropdown-item"
          >
            <FiSettings size={16} />
            Settings
          </button>
          <div className="avatar-dropdown-divider"></div>
          <button
            onClick={() => {
              onLogout();
              setShowAvatarDropdown(false);
            }}
            className="avatar-dropdown-item"
          >
            <FiLogOut size={16} />
            Logout
          </button>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col items-left justify-between md:flex-row">
            <div className="flex flex-col items-left gap-5 sm:flex-row">
              <img className="logo" src="https://rxerp.com/wp-content/uploads/2025/01/rxerp-logo-hero-tagline.svg"></img>
              <p className="mt-2 sm:mt-0 text-gray-900 text-lg font-medium mb-2">
                👋 Welcome back, {user?.first_name || user?.email}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <AvatarDropdown />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Projects Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">

              <div className="flex items-center space-x-4 justify-between flex-1">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Projects ({projects.length})
                </h3>
                {selectedProjects.size > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      {selectedProjects.size} selected
                    </span>
                    <button
                      onClick={handleBatchDelete}
                      disabled={batchDeleteLoading}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                    >
                      {batchDeleteLoading ? 'Deleting...' : 'Delete Selected'}
                    </button>
                  </div>
                )}
                <button
                onClick={handleCreateProjectClick}
                className="btn-new-project bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <FiPlus size={16} />
                New Project
              </button>
              </div>
              

          </div>
          
          {sortedProjects.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-12 h-12 mx-auto mb-4 text-gray-400">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
              <p className="text-gray-500 mb-4">Get started by creating your first EPCIS project.</p>
              <button
                onClick={handleCreateProjectClick}
                className="btn-new-project bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium"
              >
                <FiPlus size={16} />
                Create First Project
              </button>
            </div>
          ) : (
            <>
              {/* Select All Header */}
              {projects.length > 0 && (
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 ">
                  <div className="flex items-center justify-between">
                    <div className='flex items-center'><input
                      type="checkbox"
                      checked={isAllSelected}
                      onChange={handleSelectAll}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-3 text-sm font-medium text-gray-700">
                      Select all on this page
                    </label>
                    </div>
                    <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="updated_at">Last Modified</option>
                  <option value="created_at">Created Date</option>
                  <option value="name">Name</option>
                  <option value="status">Status</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
                  </div>
                </div>
              )}
              
              {/* Desktop Table View */}
              <ul className="divide-y divide-gray-200 project-table">
                {getCurrentPageProjects().map((project) => {
                  const totals = calculateProjectTotals(project.configuration);
                  
                  return (
                    <li key={project.id} className="px-4 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={selectedProjects.has(project.id)}
                            onChange={() => handleSelectProject(project.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center">
                              <h4 className="text-lg font-medium text-gray-900 truncate">
                                {project.name}
                              </h4>
                              <button
                                onClick={() => handleRenameClick(project)}
                                className="ml-2 p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                                title="Rename project"
                              >
                                <FiEdit2 size={14} />
                              </button>
                              <span className={`ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                project.status === 'Completed' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {project.status}
                              </span>
                            </div>
                            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                              <span>Step {project.current_step} of 3</span>
                              <span>•</span>
                              <span>Modified {new Date(project.updated_at).toLocaleDateString()}</span>
                              <span>•</span>
                              <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                            </div>
                            
                            {/* Package Hierarchy - Only show if packaging configuration is set and locked */}
                            {isPackagingConfigSetAndLocked(project) && (
                              <div className="mt-2 flex items-center space-x-2 text-sm text-gray-600">
                                <span className="font-medium">Package Hierarchy:</span>
                                <div className="flex items-center space-x-1">
                                  <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                                    {project.configuration.numberOfSscc || 0} SSCC{(project.configuration.numberOfSscc || 0) !== 1 ? 's' : ''}
                                  </span>
                                  
                                  {project.configuration.casesPerSscc > 0 && (
                                    <>
                                      <span className="text-gray-400">→</span>
                                      <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                                        {totals.totalCases} Case{totals.totalCases !== 1 ? 's' : ''}
                                      </span>
                                    </>
                                  )}
                                  
                                  {project.configuration.useInnerCases && (
                                    <>
                                      <span className="text-gray-400">→</span>
                                      <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                                        {totals.totalInnerCases} Inner Case{totals.totalInnerCases !== 1 ? 's' : ''}
                                      </span>
                                    </>
                                  )}
                                  
                                  <span className="text-gray-400">→</span>
                                  <span className="bg-blue-100 px-2 py-1 rounded text-xs text-blue-800">
                                    {totals.totalItems} Item{totals.totalItems !== 1 ? 's' : ''}
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                        {project.status !== 'Completed' && (
                          <button
                            onClick={() => onSelectProject(project)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium"
                          >
                            Resume
                          </button>
                        )}
                        {project.status === 'Completed' && (
                          <button
                            onClick={() => handleDownloadEPCIS(project.id)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium"
                          >
                            Download
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteProject(project.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            
            {/* Mobile Card View */}
            <div className="project-cards">
              {getCurrentPageProjects().map((project) => {
                const totals = calculateProjectTotals(project.configuration);
                
                return (
                  <div key={project.id} className="project-card">
                    <div className="project-card-header">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={selectedProjects.has(project.id)}
                          onChange={() => handleSelectProject(project.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <h4 className="project-card-title">
                          {project.name}
                        </h4>
                        <button
                          onClick={() => handleRenameClick(project)}
                          className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                          title="Rename project"
                        >
                          <FiEdit2 size={14} />
                        </button>
                      </div>
                      <span className={`project-card-status ${
                        project.status === 'Completed' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    
                    <div className="project-card-info">
                      <div className="project-card-info-item">
                        <span className="project-card-info-label">Progress:</span>
                        <span className="project-card-info-value">Step {project.current_step} of 3</span>
                      </div>
                      <div className="project-card-info-item">
                        <span className="project-card-info-label">Modified:</span>
                        <span className="project-card-info-value">{new Date(project.updated_at).toLocaleDateString()}</span>
                      </div>
                      <div className="project-card-info-item">
                        <span className="project-card-info-label">Created:</span>
                        <span className="project-card-info-value">{new Date(project.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    {/* Mobile Package Hierarchy */}
                    {isPackagingConfigSetAndLocked(project) && (
                      <div className="package-hierarchy">
                        <div className="font-medium text-gray-700 mb-2">Package Hierarchy:</div>
                        <div className="flex flex-col space-y-1">
                          <div className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {project.configuration.numberOfSscc || 0} SSCC{(project.configuration.numberOfSscc || 0) !== 1 ? 's' : ''}
                          </div>
                          
                          {project.configuration.casesPerSscc > 0 && (
                            <>
                              <div className="hierarchy-arrow">↓</div>
                              <div className="bg-gray-100 px-2 py-1 rounded text-xs">
                                {totals.totalCases} Case{totals.totalCases !== 1 ? 's' : ''}
                              </div>
                            </>
                          )}
                          
                          {project.configuration.useInnerCases && (
                            <>
                              <div className="hierarchy-arrow">↓</div>
                              <div className="bg-gray-100 px-2 py-1 rounded text-xs">
                                {totals.totalInnerCases} Inner Case{totals.totalInnerCases !== 1 ? 's' : ''}
                              </div>
                            </>
                          )}
                          
                          <div className="hierarchy-arrow">↓</div>
                          <div className="bg-blue-100 px-2 py-1 rounded text-xs text-blue-800">
                            {totals.totalItems} Item{totals.totalItems !== 1 ? 's' : ''}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div className="project-card-actions">
                      {project.status !== 'Completed' && (
                        <button
                          onClick={() => onSelectProject(project)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm font-medium"
                        >
                          Resume
                        </button>
                      )}
                      {project.status === 'Completed' && (
                        <button
                          onClick={() => handleDownloadEPCIS(project.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm font-medium"
                        >
                          Download
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Pagination */}
            {projects.length > projectsPerPage && (
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-700">
                      Showing {((currentPage - 1) * projectsPerPage) + 1} to {Math.min(currentPage * projectsPerPage, projects.length)} of {projects.length} projects
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    
                    {/* Page numbers */}
                    <div className="flex items-center space-x-1">
                      {Array.from({ length: getTotalPages() }, (_, i) => i + 1).map((page) => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`relative inline-flex items-center px-3 py-1 border text-sm font-medium rounded-md ${
                            currentPage === page
                              ? 'z-10 bg-blue-600 border-blue-600 text-white'
                              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                    
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === getTotalPages()}
                      className="relative inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
          )}
        </div>
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Create New Project</h3>
              <div className="mt-4">
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleCreateProject()}
                />
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleCreateProject}
                  disabled={createLoading || !newProjectName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {createLoading ? 'Creating...' : 'Create Project'}
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="mt-2 px-4 py-2 bg-gray-300 text-gray-700 text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rename Project Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Rename Project</h3>
              <div className="mt-4">
                <input
                  type="text"
                  value={renameProjectName}
                  onChange={(e) => setRenameProjectName(e.target.value)}
                  placeholder="Enter new project name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleRenameProject()}
                  autoFocus
                />
              </div>
              <div className="mt-4 flex justify-center space-x-4">
                <button
                  onClick={handleRenameProject}
                  disabled={renameLoading || !renameProjectName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {renameLoading ? 'Renaming...' : 'Rename Project'}
                </button>
                <button
                  onClick={handleCancelRename}
                  className="mt-2 px-4 py-2 bg-gray-300 text-gray-700 text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Settings Modal */}
      {showUserSettings && (
        <UserSettings onClose={() => setShowUserSettings(false)} />
      )}
    </div>
  );
};

export default ProjectDashboard;