import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Database, 
  Package, 
  Truck, 
  Warehouse, 
  Users, 
  RefreshCw,
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  MapPin,
  Star,
  Phone,
  Mail,
  Clock,
  Shield,
  Box,
  Tag,
  DollarSign
} from 'lucide-react';
import { api } from '../services/api';

type TabType = 'suppliers' | 'products' | 'inventory' | 'warehouses';

interface Supplier {
  supplier_id: string;
  name: string;
  short_name?: string;
  region?: string;
  province?: string;
  city?: string;
  address?: string;
  rating: number;
  rating_count: number;
  main_category?: string;
  contact?: string;
  phone?: string;
  email?: string;
  payment_terms?: string;
  min_order_amount: number;
  delivery_days: number;
  certifications: string[];
  status: string;
  cooperation_years: number;
}

interface Product {
  sku: string;
  name: string;
  category?: string;
  sub_category?: string;
  base_price: number;
  currency: string;
  unit?: string;
  specifications: Record<string, any>;
  description?: string;
  safety_stock: number;
  status: string;
}

interface Inventory {
  sku: string;
  warehouse_id: string;
  quantity: number;
  available: number;
  reserved: number;
  location?: string;
  batch_number?: string;
  status: string;
}

interface Warehouse {
  warehouse_id: string;
  name: string;
  region?: string;
  province?: string;
  city?: string;
  address?: string;
  capacity_sqm?: number;
  type?: string;
  manager?: string;
  phone?: string;
  status: string;
}

export function DataViewer() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabType>('suppliers');
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState({
    total_suppliers: 0,
    total_products: 0,
    total_inventory: 0,
    total_warehouses: 0,
    total_orders: 0,
    total_logistics: 0,
  });
  
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  useEffect(() => {
    loadSummary();
    loadData();
  }, [activeTab]);

  const loadSummary = async () => {
    try {
      const data = await api.getDatabaseSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'suppliers':
          const suppliersData = await api.getSuppliers();
          setSuppliers(suppliersData.suppliers);
          break;
        case 'products':
          const productsData = await api.getProducts();
          setProducts(productsData.products);
          break;
        case 'inventory':
          const inventoryData = await api.getInventory();
          setInventory(inventoryData.inventory);
          break;
        case 'warehouses':
          const warehousesData = await api.getWarehouses();
          setWarehouses(warehousesData.warehouses);
          break;
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'suppliers', label: t('dataViewer.suppliers'), icon: Users, count: summary.total_suppliers },
    { id: 'products', label: t('dataViewer.products'), icon: Package, count: summary.total_products },
    { id: 'inventory', label: t('dataViewer.inventory'), icon: Box, count: summary.total_inventory },
    { id: 'warehouses', label: t('dataViewer.warehouses'), icon: Warehouse, count: summary.total_warehouses },
  ];

  const renderSupplierCard = (supplier: Supplier) => {
    const isExpanded = expandedItem === supplier.supplier_id;
    return (
      <div 
        key={supplier.supplier_id}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setExpandedItem(isExpanded ? null : supplier.supplier_id)}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{supplier.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{supplier.supplier_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 text-yellow-500">
              <Star className="w-4 h-4 fill-current" />
              <span className="text-sm font-medium">{supplier.rating}</span>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.region')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.region || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.category')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.main_category || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.contact')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.contact || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.phone')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.phone || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.paymentTerms')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.payment_terms || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.minOrder')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  ¥{supplier.min_order_amount.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.deliveryDays')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {supplier.delivery_days} {t('dataViewer.days')}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.status')}</p>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  supplier.status === 'active' 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}>
                  {supplier.status === 'active' ? t('dataViewer.active') : t('dataViewer.inactive')}
                </span>
              </div>
            </div>
            {supplier.certifications && supplier.certifications.length > 0 && (
              <div className="mt-4 flex items-center gap-2">
                <Shield className="w-4 h-4 text-green-600" />
                <div className="flex gap-1">
                  {supplier.certifications.map((cert, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded">
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderProductCard = (product: Product) => {
    const isExpanded = expandedItem === product.sku;
    return (
      <div 
        key={product.sku}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setExpandedItem(isExpanded ? null : product.sku)}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
              <Package className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{product.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{product.sku}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 text-green-600">
              <DollarSign className="w-4 h-4" />
              <span className="text-sm font-medium">¥{product.base_price}</span>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.category')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {product.category || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.subCategory')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {product.sub_category || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.unit')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {product.unit || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.safetyStock')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {product.safety_stock.toLocaleString()}
                </p>
              </div>
            </div>
            {product.description && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.description')}</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">{product.description}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderInventoryCard = (item: Inventory) => {
    const isExpanded = expandedItem === `${item.sku}-${item.warehouse_id}`;
    return (
      <div 
        key={`${item.sku}-${item.warehouse_id}`}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setExpandedItem(isExpanded ? null : `${item.sku}-${item.warehouse_id}`)}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
              <Box className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{item.sku}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{item.warehouse_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {item.quantity.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.quantity')}</p>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.available')}</p>
                <p className="text-sm font-medium text-green-600">{item.available.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.reserved')}</p>
                <p className="text-sm font-medium text-orange-600">{item.reserved.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.location')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {item.location || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.batchNumber')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {item.batch_number || '-'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderWarehouseCard = (warehouse: Warehouse) => {
    const isExpanded = expandedItem === warehouse.warehouse_id;
    return (
      <div 
        key={warehouse.warehouse_id}
        className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 mb-3 overflow-hidden hover:shadow-md transition-shadow"
      >
        <div 
          className="p-4 cursor-pointer flex items-center justify-between"
          onClick={() => setExpandedItem(isExpanded ? null : warehouse.warehouse_id)}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
              <Warehouse className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">{warehouse.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{warehouse.warehouse_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <MapPin className="w-4 h-4" />
              <span className="text-sm">{warehouse.city || warehouse.region || '-'}</span>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.region')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {warehouse.region || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.type')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {warehouse.type || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.capacity')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {warehouse.capacity_sqm ? `${warehouse.capacity_sqm.toLocaleString()} m²` : '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.manager')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {warehouse.manager || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.phone')}</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {warehouse.phone || '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.status')}</p>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  warehouse.status === 'active' 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}>
                  {warehouse.status === 'active' ? t('dataViewer.active') : t('dataViewer.inactive')}
                </span>
              </div>
            </div>
            {warehouse.address && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('dataViewer.address')}</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">{warehouse.address}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const filteredData = () => {
    let data: any[] = [];
    switch (activeTab) {
      case 'suppliers':
        data = suppliers;
        break;
      case 'products':
        data = products;
        break;
      case 'inventory':
        data = inventory;
        break;
      case 'warehouses':
        data = warehouses;
        break;
    }
    
    if (!searchTerm) return data;
    
    return data.filter((item) => {
      const searchLower = searchTerm.toLowerCase();
      if (activeTab === 'suppliers') {
        return (
          item.name?.toLowerCase().includes(searchLower) ||
          item.supplier_id?.toLowerCase().includes(searchLower) ||
          item.region?.toLowerCase().includes(searchLower)
        );
      }
      if (activeTab === 'products') {
        return (
          item.name?.toLowerCase().includes(searchLower) ||
          item.sku?.toLowerCase().includes(searchLower) ||
          item.category?.toLowerCase().includes(searchLower)
        );
      }
      if (activeTab === 'inventory') {
        return (
          item.sku?.toLowerCase().includes(searchLower) ||
          item.warehouse_id?.toLowerCase().includes(searchLower)
        );
      }
      if (activeTab === 'warehouses') {
        return (
          item.name?.toLowerCase().includes(searchLower) ||
          item.warehouse_id?.toLowerCase().includes(searchLower) ||
          item.city?.toLowerCase().includes(searchLower)
        );
      }
      return true;
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Database className="w-7 h-7" />
          {t('dataViewer.title')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('dataViewer.subtitle')}</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
            <Users className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.suppliers')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_suppliers}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
            <Package className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.products')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_products}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <Box className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.inventory')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_inventory}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
            <Warehouse className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.warehouses')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_warehouses}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <Tag className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.orders')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_orders}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400">
            <Truck className="w-5 h-5" />
            <span className="text-sm">{t('dataViewer.logistics')}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{summary.total_logistics}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700">
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder={t('dataViewer.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : (
            <div className="space-y-2">
              {filteredData().length === 0 ? (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  {t('dataViewer.noData')}
                </div>
              ) : (
                filteredData().map((item) => {
                  switch (activeTab) {
                    case 'suppliers':
                      return renderSupplierCard(item as Supplier);
                    case 'products':
                      return renderProductCard(item as Product);
                    case 'inventory':
                      return renderInventoryCard(item as Inventory);
                    case 'warehouses':
                      return renderWarehouseCard(item as Warehouse);
                    default:
                      return null;
                  }
                })
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DataViewer;
