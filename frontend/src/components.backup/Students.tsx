import { useState, useEffect } from 'react';
import { getStudents, createStudent, updateStudent, deleteStudent } from '../services/api';
import type { Student } from '../types';

function Students() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [formData, setFormData] = useState({
    xml_id: 0,
    name: '',
    email: ''
  });

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      setLoading(true);
      const response = await getStudents();
      setStudents(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los estudiantes');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingStudent) {
        await updateStudent(editingStudent.id, formData);
      } else {
        await createStudent(formData);
      }
      await loadStudents();
      setShowModal(false);
      resetForm();
    } catch (err) {
      setError('Error al guardar el estudiante');
      console.error(err);
    }
  };

  const handleEdit = (student: Student) => {
    setEditingStudent(student);
    setFormData({
      xml_id: student.xml_id,
      name: student.name,
      email: student.email || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Estás seguro de eliminar este estudiante?')) {
      try {
        await deleteStudent(id);
        await loadStudents();
      } catch (err) {
        setError('Error al eliminar el estudiante');
        console.error(err);
      }
    }
  };

  const resetForm = () => {
    setEditingStudent(null);
    setFormData({
      xml_id: 0,
      name: '',
      email: ''
    });
  };

  if (loading) return <div className="loading">Cargando estudiantes...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>👨‍🎓 Gestión de Estudiantes</h2>
        <button 
          className="btn btn-primary" 
          onClick={() => { resetForm(); setShowModal(true); }}
        >
          + Agregar Estudiante
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
                <th>Clases Inscritas</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay estudiantes registrados. Importa un archivo XML o agrega manualmente.
                  </td>
                </tr>
              ) : (
                students.map(student => (
                  <tr key={student.id}>
                    <td>{student.xml_id}</td>
                    <td>{student.name}</td>
                    <td>{student.email || '-'}</td>
                    <td>
                      <span className="badge badge-primary">{student.enrolled_classes_count || 0}</span>
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary" 
                        onClick={() => handleEdit(student)}
                        style={{ marginRight: '0.5rem' }}
                      >
                        Editar
                      </button>
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleDelete(student.id)}
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
              <h3>{editingStudent ? 'Editar Estudiante' : 'Agregar Estudiante'}</h3>
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
                  {editingStudent ? 'Actualizar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Students;
