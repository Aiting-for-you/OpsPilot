import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Wrench, 
  Plus, 
  Search, 
  RefreshCw, 
  Edit2, 
  Trash2, 
  Power,
  ChevronDown,
  ChevronRight,
  Code,
  Tag,
  User,
  Calendar,
  Check,
  X,
  Copy,
  Download,
  Upload,
  Cloud,
  Star,
  Eye,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';

interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  enabled: boolean;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  parameters: Array<Record<string, any>>;
  examples: Array<Record<string, any>>;
  tags: string[];
  author?: string;
  created_at?: string;
  updated_at?: string;
}

interface CloudSkill {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  author: string;
  downloads: number;
  rating: number;
  tags: string[];
  created_at?: string;
}

interface Category {
  name: string;
  count: number;
}

type TabType = 'local' | 'cloud';

export function SkillsManager() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>('local');
  const [loading, setLoading] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [cloudSkills, setCloudSkills] = useState<CloudSkill[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [cloudCategories, setCloudCategories] = useState<Category[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadMessage, setDownloadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    version: '1.0.0',
    tags: '',
    author: '',
    parameters: '',
    examples: '',
  });

  useEffect(() => {
    loadSkills();
    loadCategories();
    if (activeTab === 'cloud') {
      loadCloudSkills();
      loadCloudCategories();
    }
  }, [activeTab]);

  const loadSkills = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      const data = await api.getSkills(params);
      setSkills(data.skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api.getSkillCategories();
      setCategories(data.categories);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const loadCloudSkills = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      if (searchTerm) {
        params.search = searchTerm;
      }
      const data = await api.getCloudSkills(params);
      setCloudSkills(data.skills);
    } catch (error) {
      console.error('Failed to load cloud skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCloudCategories = async () => {
    try {
      const data = await api.getCloudSkillCategories();
      setCloudCategories(data.categories);
    } catch (error) {
      console.error('Failed to load cloud categories:', error);
    }
  };

  const handleToggleSkill = async (skillId: string) => {
    try {
      await api.toggleSkill(skillId);
      loadSkills();
    } catch (error) {
      console.error('Failed to toggle skill:', error);
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    try {
      await api.deleteSkill(skillId);
      setShowDeleteConfirm(null);
      loadSkills();
      loadCategories();
    } catch (error) {
      console.error('Failed to delete skill:', error);
    }
  };

  const handleDownloadSkill = async (skillId: string) => {
    try {
      setDownloadingId(skillId);
      setDownloadMessage(null);
      const result = await api.downloadCloudSkill(skillId);
      
      if (result.success) {
        setDownloadMessage({ type: 'success', text: result.message });
        loadSkills();
        loadCategories();
      } else {
        setDownloadMessage({ type: 'error', text: result.message });
      }
    } catch (error: any) {
      setDownloadMessage({ type: 'error', text: error.message || t('skillsManager.downloadFailed') });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleCreateSkill = async () => {
    try {
      let parameters = [];
      let examples = [];
      
      try {
        parameters = formData.parameters ? JSON.parse(formData.parameters) : [];
      } catch {
        alert(t('skillsManager.invalidJson'));
        return;
      }
      
      try {
        examples = formData.examples ? JSON.parse(formData.examples) : [];
      } catch {
        alert(t('skillsManager.invalidJson'));
        return;
      }

      await api.createSkill({
        name: formData.name,
        description: formData.description,
        category: formData.category,
        version: formData.version,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t),
        author: formData.author,
        parameters,
        examples,
      });
      
      setShowCreateModal(false);
      resetForm();
      loadSkills();
      loadCategories();
    } catch (error) {
      console.error('Failed to create skill:', error);
    }
  };

  const handleUpdateSkill = async () => {
    if (!editingSkill) return;
    
    try {
      let parameters = [];
      let examples = [];
      
      try {
        parameters = formData.parameters ? JSON.parse(formData.parameters) : [];
      } catch {
        alert(t('skillsManager.invalidJson'));
        return;
      }
      
      try {
        examples = formData.examples ? JSON.parse(formData.examples) : [];
      } catch {
        alert(t('skillsManager.invalidJson'));
        return;
      }

      await api.updateSkill(editingSkill.id, {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        version: formData.version,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t),
        author: formData.author,
        parameters,
        examples,
      });
      
      setEditingSkill(null);
      resetForm();
      loadSkills();
      loadCategories();
    } catch (error) {
      console.error('Failed to update skill:', error);
    }
  };

  const openEditModal = (skill: Skill) => {
    setFormData({
      name: skill.name,
      description: skill.description,
      category: skill.category,
      version: skill.version,
      tags: skill.tags.join(', '),
      author: skill.author || '',
      parameters: JSON.stringify(skill.parameters, null, 2),
      examples: JSON.stringify(skill.examples, null, 2),
    });
    setEditingSkill(skill);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: '',
      version: '1.0.0',
      tags: '',
      author: '',
      parameters: '',
      examples: '',
    });
  };

  const filteredSkills = () => {
    let result = skills;
    
    if (selectedCategory) {
      result = result.filter(s => s.category === selectedCategory);
    }
    
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      result = result.filter(s => 
        s.name.toLowerCase().includes(searchLower) ||
        s.description.toLowerCase().includes(searchLower) ||
        s.tags.some(t => t.toLowerCase().includes(searchLower))
      );
    }
    
    return result;
  };

  const filteredCloudSkills = () => {
    let result = cloudSkills;
    
    if (selectedCategory) {
      result = result.filter(s => s.category === selectedCategory);
    }
    
    return result;
  };

  const isSkillDownloaded = (skillId: string) => {
    return skills.some(s => s.id === skillId);
  };

  const renderSkillCard = (skill: Skill) => {
    const isExpanded = expandedSkill === skill.id;
    return (
      <div 
        key={skill.id}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setExpandedSkill(isExpanded ? null : skill.id)}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              skill.enabled 
                ? 'bg-green-100 dark:bg-green-900' 
                : 'bg-gray-100 dark:bg-gray-700'
            }`}>
              <Wrench className={`w-5 h-5 ${
                skill.enabled 
                  ? 'text-green-600 dark:text-green-400' 
                  : 'text-gray-400'
              }`} />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{skill.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{skill.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 text-xs rounded ${
              skill.enabled 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
            }`}>
              {skill.enabled ? t('skillsManager.enabled') : t('skillsManager.disabled')}
            </span>
            <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              v{skill.version}
            </span>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{skill.description}</p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.category')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{skill.category}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.parameters')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {skill.parameters.length}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.examples')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {skill.examples.length}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.author')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {skill.author || '-'}
                </p>
              </div>
            </div>
            
            {skill.tags && skill.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {skill.tags.map((tag, idx) => (
                  <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {skill.parameters && skill.parameters.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('skillsManager.parameters')}</p>
                <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto">
                  {JSON.stringify(skill.parameters, null, 2)}
                </pre>
              </div>
            )}
            
            {skill.examples && skill.examples.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('skillsManager.examples')}</p>
                <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto">
                  {JSON.stringify(skill.examples, null, 2)}
                </pre>
              </div>
            )}
            
            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleSkill(skill.id);
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded text-sm ${
                  skill.enabled 
                    ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600' 
                    : 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800'
                }`}
              >
                <Power className="w-4 h-4" />
                {skill.enabled ? t('skillsManager.disable') : t('skillsManager.enable')}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openEditModal(skill);
                }}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-sm bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800"
              >
                <Edit2 className="w-4 h-4" />
                {t('skillsManager.edit')}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDeleteConfirm(skill.id);
                }}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-sm bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800"
              >
                <Trash2 className="w-4 h-4" />
                {t('skillsManager.delete')}
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCloudSkillCard = (cloudSkill: CloudSkill) => {
    const isDownloaded = isSkillDownloaded(cloudSkill.id);
    const isDownloading = downloadingId === cloudSkill.id;
    
    return (
      <div 
        key={cloudSkill.id}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Cloud className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{cloudSkill.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">v{cloudSkill.version}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isDownloaded ? (
              <span className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                <CheckCircle className="w-3 h-3" />
                {t('skillsManager.downloaded')}
              </span>
            ) : (
              <button
                onClick={() => handleDownloadSkill(cloudSkill.id)}
                disabled={isDownloading}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDownloading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    {t('skillsManager.downloading')}
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    {t('skillsManager.download')}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        
        <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{cloudSkill.description}</p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.category')}</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{cloudSkill.category}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.author')}</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{cloudSkill.author}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.downloads')}</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{cloudSkill.downloads}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('skillsManager.rating')}</p>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                {cloudSkill.rating}
              </p>
            </div>
          </div>
          
          {cloudSkill.tags && cloudSkill.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {cloudSkill.tags.map((tag, idx) => (
                <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Wrench className="w-7 h-7" />
            {t('skillsManager.title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('skillsManager.subtitle')}</p>
        </div>
        {activeTab === 'local' && (
          <button
            onClick={() => {
              resetForm();
              setShowCreateModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            {t('skillsManager.createSkill')}
          </button>
        )}
      </div>

      {/* Tab & Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        {/* Tab Switcher */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => {
              setActiveTab('local');
              setSearchTerm('');
              setSelectedCategory('');
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'local'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            <Wrench className="w-4 h-4" />
            {t('skillsManager.localSkills')}
          </button>
          <button
            onClick={() => {
              setActiveTab('cloud');
              setSearchTerm('');
              setSelectedCategory('');
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'cloud'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            <Cloud className="w-4 h-4" />
            {t('skillsManager.cloudMarket')}
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded">
              {cloudSkills.length}
            </span>
          </button>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder={activeTab === 'local' ? t('skillsManager.searchPlaceholder') : t('skillsManager.cloudSearchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="min-w-[200px]">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t('skillsManager.allCategories')}</option>
              {(activeTab === 'local' ? categories : cloudCategories).map((cat) => (
                <option key={cat.name} value={cat.name}>
                  {cat.name} ({cat.count})
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={activeTab === 'local' ? loadSkills : loadCloudSkills}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {t('skillsManager.refresh')}
          </button>
        </div>
      </div>

      {/* Download Message */}
      {downloadMessage && (
        <div className={`mb-4 p-4 rounded-lg flex items-center gap-2 ${
          downloadMessage.type === 'success' 
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        }`}>
          {downloadMessage.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          {downloadMessage.text}
          <button 
            onClick={() => setDownloadMessage(null)}
            className="ml-auto hover:opacity-70"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Skills List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {activeTab === 'local' 
                ? `${t('skillsManager.totalSkills')}: ${filteredSkills().length}`
                : `${t('skillsManager.cloudTotal')}: ${filteredCloudSkills().length}`
              }
            </p>
            {activeTab === 'local' && (
              <button
                onClick={() => {
                  resetForm();
                  setShowCreateModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                {t('skillsManager.createSkill')}
              </button>
            )}
          </div>
        </div>
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : activeTab === 'local' ? (
            filteredSkills().length === 0 ? (
              <div className="text-center py-12">
                <Wrench className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">{t('skillsManager.noSkills')}</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  {t('skillsManager.createFirst')}
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredSkills().map(renderSkillCard)}
              </div>
            )
          ) : (
            filteredCloudSkills().length === 0 ? (
              <div className="text-center py-12">
                <Cloud className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">{t('skillsManager.noCloudSkills')}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredCloudSkills().map(renderCloudSkillCard)}
              </div>
            )
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingSkill) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                {editingSkill ? t('skillsManager.editSkill') : t('skillsManager.createNewSkill')}
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.name')} *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder={t('skillsManager.namePlaceholder')}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.description')} *
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder={t('skillsManager.descriptionPlaceholder')}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {t('skillsManager.category')} *
                    </label>
                    <input
                      type="text"
                      value={formData.category}
                      onChange={(e) => setFormData({...formData, category: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={t('skillsManager.categoryPlaceholder')}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {t('skillsManager.version')}
                    </label>
                    <input
                      type="text"
                      value={formData.version}
                      onChange={(e) => setFormData({...formData, version: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="1.0.0"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.tags')}
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({...formData, tags: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder={t('skillsManager.tagsPlaceholder')}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.author')}
                  </label>
                  <input
                    type="text"
                    value={formData.author}
                    onChange={(e) => setFormData({...formData, author: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder={t('skillsManager.authorPlaceholder')}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.parameters')} (JSON)
                  </label>
                  <textarea
                    value={formData.parameters}
                    onChange={(e) => setFormData({...formData, parameters: e.target.value})}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-mono text-sm"
                    placeholder='[{"name": "param1", "type": "string", "required": true}]'
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('skillsManager.examples')} (JSON)
                  </label>
                  <textarea
                    value={formData.examples}
                    onChange={(e) => setFormData({...formData, examples: e.target.value})}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-mono text-sm"
                    placeholder='[{"input": {...}, "output": {...}}]'
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingSkill(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={editingSkill ? handleUpdateSkill : handleCreateSkill}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingSkill ? t('common.save') : t('skillsManager.create')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {t('skillsManager.confirmDelete')}
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              {t('skillsManager.deleteWarning')}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => handleDeleteSkill(showDeleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                {t('common.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SkillsManager;
