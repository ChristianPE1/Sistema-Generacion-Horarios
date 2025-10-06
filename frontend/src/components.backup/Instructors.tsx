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

  if (loading) return <div className="loading">Cargando instructores...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>👨‍🏫 Gestión de Instructores</h2>
        <button 
          className="btn btn-primary" 
          onClick={() => { resetForm(); setShowModal(true); }}
        >
          + Agregar Instructor
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID XML</th>
                <th>Nombre</th>
                <th>Email</th>
                <th>Clases</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {instructors.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay instructores registrados. Importa un archivo XML o agrega manualmente.
                  </td>
                </tr>
              ) : (
                instructors.map(instructor => (
                  <tr key={instructor.id}>
                    <td>{instructor.xml_id}</td>
                    <td>{instructor.name}</td>
                    <td>{instructor.email || '-'}</td>
                    <td>
                      <span className="badge badge-primary">{instructor.class_count || 0}</span>
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary" 
                        onClick={() => handleEdit(instructor)}
                        style={{ marginRight: '0.5rem' }}
                      >
                        Editar
                      </button>
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleDelete(instructor.id)}
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
              <h3>{editingInstructor ? 'Editar Instructor' : 'Agregar Instructor'}</h3>
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
                <label className="form-label">Nombre</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-success">
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
