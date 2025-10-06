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
      location: room.location,
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

  if (loading) return <div className="loading">Cargando aulas...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>🏫 Gestión de Aulas</h2>
        <button 
          className="btn btn-primary" 
          onClick={() => { resetForm(); setShowModal(true); }}
        >
          + Agregar Aula
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID XML</th>
                <th>Capacidad</th>
                <th>Ubicación</th>
                <th>Con Restricción</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rooms.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay aulas registradas. Importa un archivo XML o agrega manualmente.
                  </td>
                </tr>
              ) : (
                rooms.map(room => (
                  <tr key={room.id}>
                    <td>{room.xml_id}</td>
                    <td>{room.capacity}</td>
                    <td>{room.location || '-'}</td>
                    <td>
                      <span className={`badge ${room.is_constraint ? 'badge-success' : 'badge-secondary'}`}>
                        {room.is_constraint ? 'Sí' : 'No'}
                      </span>
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary" 
                        onClick={() => handleEdit(room)}
                        style={{ marginRight: '0.5rem' }}
                      >
                        Editar
                      </button>
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleDelete(room.id)}
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
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRoom ? 'Editar Aula' : 'Agregar Aula'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">ID XML</label>
                <input
                  type="number"
                  className="form-control"
                  value={formData.xml_id}
                  onChange={(e) => setFormData({...formData, xml_id: parseInt(e.target.value)})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Capacidad</label>
                <input
                  type="number"
                  className="form-control"
                  value={formData.capacity}
                  onChange={(e) => setFormData({...formData, capacity: parseInt(e.target.value)})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Ubicación</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="checkbox"
                    checked={formData.is_constraint}
                    onChange={(e) => setFormData({...formData, is_constraint: e.target.checked})}
                    style={{ marginRight: '0.5rem' }}
                  />
                  Tiene restricciones
                </label>
              </div>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-success">
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
