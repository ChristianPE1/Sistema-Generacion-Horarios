import { useState, useEffect } from 'react';
import { getRooms, createRoom, updateRoom, deleteRoom } from '../services/api';
import type { Room } from '../types';

function Rooms() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [formData, setFormData] = useState({
    xml_id: 0,
    capacity: 0,
    location: '',
    is_constraint: false
  });

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const response = await getRooms();
      setRooms(response.data);
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
      } else {
        await createRoom(formData);
      }
      await loadRooms();
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
      capacity: room.capacity,
      location: room.location || '',
      is_constraint: room.is_constraint
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Estás seguro de eliminar esta aula?')) {
      try {
        await deleteRoom(id);
        await loadRooms();
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
      capacity: 0,
      location: '',
      is_constraint: false
    });
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando aulas...</div>
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Gestión de Aulas</h2>
        <button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition font-medium"
        >
          + Agregar Aula
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capacidad</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ubicación</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Restricción</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rooms.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No hay aulas registradas. Importa un archivo XML o agrega manualmente.
                  </td>
                </tr>
              ) : (
                rooms.map(room => (
                  <tr key={room.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{room.xml_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{room.capacity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{room.location || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded ${room.is_constraint ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                        {room.is_constraint ? 'Sí' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button 
                        onClick={() => handleEdit(room)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        Editar
                      </button>
                      <button 
                        onClick={() => handleDelete(room.id)}
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
                {editingRoom ? 'Editar Aula' : 'Agregar Aula'}
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Capacidad</label>
                <input
                  type="number"
                  value={formData.capacity}
                  onChange={(e) => setFormData({...formData, capacity: parseInt(e.target.value)})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ubicación</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_constraint"
                  checked={formData.is_constraint}
                  onChange={(e) => setFormData({...formData, is_constraint: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_constraint" className="ml-2 block text-sm text-gray-700">
                  ¿Es restricción?
                </label>
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
                  {editingRoom ? 'Actualizar' : 'Crear'}
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
