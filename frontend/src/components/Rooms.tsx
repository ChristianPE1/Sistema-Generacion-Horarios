import { useState, useEffect } from 'react';
import { getRooms, updateRoom, deleteRoom } from '../services/api';
import type { Room } from '../types';
import type { PaginatedResponse } from '../services/api';
import Pagination from './Pagination';
import { 
  Building2, 
  Users, 
  Pencil, 
  Trash2, 
  X,
  Loader2,
  AlertCircle,
  Search
} from 'lucide-react';

function Rooms() {
  const [paginatedData, setPaginatedData] = useState<PaginatedResponse<Room> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    xml_id: 0,
    capacity: 0
  });

  useEffect(() => {
    loadRooms(currentPage);
  }, [currentPage]);

  const loadRooms = async (page: number) => {
    try {
      setLoading(true);
      const response = await getRooms(page, 20);
      setPaginatedData(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar las aulas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRoom) {
        await updateRoom(editingRoom.id, formData);
      }
      await loadRooms(currentPage);
      setShowModal(false);
      resetForm();
    } catch (err) {
      setError('Error al guardar el aula');
      console.error(err);
    }
  };

  const handleEdit = (room: Room) => {
    setEditingRoom(room);
    setFormData({
      xml_id: room.xml_id,
      capacity: room.capacity
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Estás seguro de eliminar esta aula?')) {
      try {
        await deleteRoom(id);
        await loadRooms(currentPage);
      } catch (err) {
        setError('Error al eliminar el aula');
        console.error(err);
      }
    }
  };

  const resetForm = () => {
    setEditingRoom(null);
    setFormData({
      xml_id: 0,
      capacity: 0
    });
  };

  // Filtrar aulas por búsqueda
  const rooms = paginatedData?.results || [];
  const filteredRooms = rooms.filter(room => 
    room.xml_id.toString().includes(searchTerm) ||
    room.capacity.toString().includes(searchTerm)
  );
  const totalPages = paginatedData ? Math.ceil(paginatedData.count / 20) : 0;

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
      <p className="text-gray-600">Cargando aulas...</p>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Gestión de Aulas</h1>
          {paginatedData && (
            <p className="text-gray-500 mt-1">
              {paginatedData.count} aulas registradas
            </p>
          )}
        </div>
        
        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar aula..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <p className="text-red-700">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Building2 className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-blue-800">
              <strong>Nota:</strong> Las aulas se importan automáticamente desde el archivo XML. 
              Puedes editar la capacidad de cada aula si es necesario.
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Desktop Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Capacidad
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRooms.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-12 text-center">
                    <Building2 className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">
                      {searchTerm ? 'No se encontraron aulas con esa búsqueda' : 'No hay aulas registradas'}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Importa un archivo XML para cargar las aulas
                    </p>
                  </td>
                </tr>
              ) : (
                filteredRooms.map(room => (
                  <tr key={room.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-lg">
                          <Building2 className="h-4 w-4 text-indigo-600" />
                        </div>
                        <span className="font-medium text-gray-900">Aula {room.xml_id}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-900">{room.capacity} personas</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleEdit(room)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </button>
                        <button 
                          onClick={() => handleDelete(room.id)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Cards */}
        <div className="md:hidden divide-y divide-gray-100">
          {filteredRooms.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Building2 className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">
                {searchTerm ? 'No se encontraron aulas' : 'No hay aulas registradas'}
              </p>
            </div>
          ) : (
            filteredRooms.map(room => (
              <div key={room.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <Building2 className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Aula {room.xml_id}</p>
                      <div className="flex items-center gap-1 text-sm text-gray-500 mt-0.5">
                        <Users className="h-3 w-3" />
                        <span>{room.capacity} personas</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button 
                      onClick={() => handleEdit(room)}
                      className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button 
                      onClick={() => handleDelete(room.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        
        {/* Pagination */}
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          itemsPerPage={20}
          totalItems={paginatedData?.count}
        />
      </div>

      {/* Edit Modal */}
      {showModal && editingRoom && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <Building2 className="h-5 w-5 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">
                  Editar Aula {editingRoom.xml_id}
                </h3>
              </div>
              <button 
                onClick={() => setShowModal(false)} 
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">ID</label>
                <input
                  type="number"
                  value={formData.xml_id}
                  disabled
                  className="w-full px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-lg text-gray-500 cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">El ID no se puede modificar</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Capacidad <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="number"
                    value={formData.capacity}
                    onChange={(e) => setFormData({...formData, capacity: parseInt(e.target.value) || 0})}
                    required
                    min={1}
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Ej: 30"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                >
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Rooms;
