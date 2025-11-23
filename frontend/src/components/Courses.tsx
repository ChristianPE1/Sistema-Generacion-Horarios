import { useState, useEffect } from 'react';
import { getCourses } from '../services/api';
import type { Course } from '../types';
import type { PaginatedResponse } from '../services/api';
import Pagination from './Pagination';

function Courses() {
  const [paginatedData, setPaginatedData] = useState<PaginatedResponse<Course> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    loadCourses(currentPage);
  }, [currentPage]);

  const loadCourses = async (page: number) => {
    try {
      setLoading(true);
      const response = await getCourses(page, 20);
      setPaginatedData(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los cursos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando cursos...</div>
    </div>
  );

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Gestión de Cursos</h2>

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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clases</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {!paginatedData?.results.length ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No hay cursos registrados. Importa un archivo XML para cargar los cursos.
                  </td>
                </tr>
              ) : (
                paginatedData.results.map(course => (
                  <tr key={course.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{course.xml_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{course.code}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{course.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                        {course.class_count || 0}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {paginatedData && (
          <Pagination
            currentPage={currentPage}
            totalPages={Math.ceil(paginatedData.count / 20)}
            onPageChange={setCurrentPage}
            totalItems={paginatedData.count}
          />
        )}
      </div>
    </div>
  );
}

export default Courses;
