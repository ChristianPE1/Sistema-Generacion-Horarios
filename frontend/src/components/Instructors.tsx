import { useState, useEffect } from 'react';
import { getInstructors, createInstructor, updateInstructor, deleteInstructor } from '../services/api';
import type { Instructor } from '../types';

function Instructors() {
  const [instructors, setInstructors] = useState<Instructor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingInstructor, setEditingInstructor] = useState<Instructor | null>(null);
  const [formData, setFormData] = useState({
    xml_id: 0,
    name: '',
    email: ''
  });

  useEffect(() => {
    loadInstructors();
  }, []);

  const loadInstructors = async () => {
    try {
      setLoading(true);
      const response = await getInstructors();
      setInstructors(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los instructores');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingInstructor) {
        await updateInstructor(editingInstructor.id, formData);
      } else {
        await createInstructor(formData);
      }
      await loadInstructors();
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
        await loadInstructors();
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

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando instructores...</div>
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Gestión de Instructores</h2>
        <button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition font-medium"
        >
          + Agregar Instructor
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID XML</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clases</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {instructors.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No hay instructores registrados. Importa un archivo XML o agrega manualmente.
                  </td>
                </tr>
              ) : (
                instructors.map(instructor => (
                  <tr key={instructor.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{instructor.xml_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{instructor.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{instructor.email || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                        {instructor.class_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button 
                        onClick={() => handleEdit(instructor)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        Editar
                      </button>
                      <button 
                        onClick={() => handleDelete(instructor.id)}
                        className="text-red-600 hover:text-red-900 font-medium"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900">
                {editingInstructor ? 'Editar Instructor' : 'Agregar Instructor'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-2xl">
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ID XML</label>
                <input
                  type="number"
                  value={formData.xml_id}
                  onChange={(e) => setFormData({...formData, xml_id: parseInt(e.target.value)})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 transition font-medium"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition font-medium"
                >
                  {editingInstructor ? 'Actualizar' : 'Crear'}
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
