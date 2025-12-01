import { useState, useEffect } from 'react';
import { getInstructors, createInstructor, updateInstructor, deleteInstructor } from '../services/api';
import type { Instructor } from '../types';
import type { PaginatedResponse } from '../services/api';
import Pagination from './Pagination';
import { 
  User, 
  Mail, 
  BookOpen, 
  Pencil, 
  Trash2, 
  X,
  Loader2,
  AlertCircle,
  Search,
  UserPlus,
  Hash
} from 'lucide-react';

function Instructors() {
  const [paginatedData, setPaginatedData] = useState<PaginatedResponse<Instructor> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingInstructor, setEditingInstructor] = useState<Instructor | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    xml_id: 0,
    name: '',
    email: ''
  });

  useEffect(() => {
    loadInstructors(currentPage);
  }, [currentPage]);

  const loadInstructors = async (page: number) => {
    try {
      setLoading(true);
      const response = await getInstructors(page, 20);
      setPaginatedData(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los instructores');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Calcular el próximo ID automáticamente
  const getNextXmlId = (): number => {
    if (!paginatedData?.results.length) return 1;
    const maxId = Math.max(...paginatedData.results.map(i => i.xml_id));
    return maxId + 1;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const dataToSend = editingInstructor 
        ? formData 
        : { ...formData, xml_id: getNextXmlId() };
        
      if (editingInstructor) {
        await updateInstructor(editingInstructor.id, dataToSend);
      } else {
        await createInstructor(dataToSend);
      }
      await loadInstructors(currentPage);
      setShowModal(false);
      resetForm();
    } catch (err) {
      setError('Error al guardar el instructor');
      console.error(err);
    }
  };

  const handleEdit = (instructor: Instructor) => {
    setEditingInstructor(instructor);
    setFormData({
      xml_id: instructor.xml_id,
      name: instructor.name,
      email: instructor.email || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Estás seguro de eliminar este instructor?')) {
      try {
        await deleteInstructor(id);
        await loadInstructors(currentPage);
      } catch (err) {
        setError('Error al eliminar el instructor');
        console.error(err);
      }
    }
  };

  const resetForm = () => {
    setEditingInstructor(null);
    setFormData({
      xml_id: 0,
      name: '',
      email: ''
    });
  };

  const openAddModal = () => {
    resetForm();
    setFormData(prev => ({ ...prev, xml_id: getNextXmlId() }));
    setShowModal(true);
  };

  // Filtrar instructores
  const instructors = paginatedData?.results || [];
  const filteredInstructors = instructors.filter(instructor => 
    instructor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    instructor.xml_id.toString().includes(searchTerm) ||
    (instructor.email && instructor.email.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  const totalPages = paginatedData ? Math.ceil(paginatedData.count / 20) : 0;

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
      <p className="text-gray-600">Cargando instructores...</p>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Gestión de Instructores</h1>
          {paginatedData && (
            <p className="text-gray-500 mt-1">
              {paginatedData.count} instructores registrados
            </p>
          )}
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar instructor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          
          {/* Add Button */}
          <button 
            onClick={openAddModal}
            className="inline-flex items-center justify-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            <UserPlus className="h-4 w-4" />
            <span className="hidden sm:inline">Agregar Instructor</span>
            <span className="sm:hidden">Agregar</span>
          </button>
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

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Desktop Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Instructor
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Clases Asignadas
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInstructors.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center">
                    <User className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">
                      {searchTerm ? 'No se encontraron instructores con esa búsqueda' : 'No hay instructores registrados'}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Importa un archivo XML o agrega instructores manualmente
                    </p>
                  </td>
                </tr>
              ) : (
                filteredInstructors.map(instructor => (
                  <tr key={instructor.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-full">
                          <User className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{instructor.name}</p>
                          <p className="text-sm text-gray-500">ID: {instructor.xml_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {instructor.email ? (
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">{instructor.email}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-gray-400" />
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
                          {instructor.class_count || 0} clases
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleEdit(instructor)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </button>
                        <button 
                          onClick={() => handleDelete(instructor.id)}
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
          {filteredInstructors.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <User className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">
                {searchTerm ? 'No se encontraron instructores' : 'No hay instructores registrados'}
              </p>
            </div>
          ) : (
            filteredInstructors.map(instructor => (
              <div key={instructor.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-full">
                      <User className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{instructor.name}</p>
                      <p className="text-sm text-gray-500">ID: {instructor.xml_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button 
                      onClick={() => handleEdit(instructor)}
                      className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button 
                      onClick={() => handleDelete(instructor.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="mt-3 ml-12 flex flex-wrap gap-3 text-sm">
                  {instructor.email && (
                    <div className="flex items-center gap-1 text-gray-500">
                      <Mail className="h-3 w-3" />
                      <span>{instructor.email}</span>
                    </div>
                  )}
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                    <BookOpen className="h-3 w-3" />
                    {instructor.class_count || 0} clases
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {paginatedData && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalItems={paginatedData.count}
          />
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  {editingInstructor ? <Pencil className="h-5 w-5 text-indigo-600" /> : <UserPlus className="h-5 w-5 text-indigo-600" />}
                </div>
                <h3 className="text-xl font-bold text-gray-900">
                  {editingInstructor ? 'Editar Instructor' : 'Agregar Instructor'}
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
              {/* ID - Solo mostrar en edición, auto-generado en creación */}
              {editingInstructor ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">ID</label>
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-lg text-gray-500">
                    <Hash className="h-4 w-4" />
                    <span>{formData.xml_id}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">El ID no se puede modificar</p>
                </div>
              ) : (
                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-indigo-700">
                    <Hash className="h-4 w-4" />
                    <span>ID asignado automáticamente: <strong>{getNextXmlId()}</strong></span>
                  </div>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                    placeholder="Nombre completo del instructor"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    placeholder="correo@ejemplo.com"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">Opcional - para contacto</p>
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
                  {editingInstructor ? 'Guardar Cambios' : 'Crear Instructor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Instructors;
