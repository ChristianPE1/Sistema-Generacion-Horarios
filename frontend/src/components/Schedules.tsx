import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  getDatasets,
  generateScheduleFromDataset,
  type DatasetInfo
} from '../services/api';
import { Play, Database, Users, Building2, BookOpen, Loader2, AlertCircle } from 'lucide-react';

function Schedules() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    dataset: '',
    population_size: 50,
    generations: 100
  });

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const response = await getDatasets();
      if (response.data.success) {
        // Filtrar solo XMLs
        const xmlDatasets = response.data.datasets.filter(
          (d: DatasetInfo) => d.type === 'xml'
        );
        setDatasets(xmlDatasets);
        if (xmlDatasets.length > 0 && !formData.dataset) {
          setFormData(prev => ({ ...prev, dataset: xmlDatasets[0].name }));
        }
      }
    } catch (err) {
      setError('Error cargando datasets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.dataset) {
      setError('Seleccione un dataset');
      return;
    }
    
    try {
      setGenerating(true);
      setError(null);
      
      const response = await generateScheduleFromDataset({
        dataset: formData.dataset,
        name: `Horario - ${formData.dataset}`,
        population_size: formData.population_size,
        generations: formData.generations
      });
      
      if (response.data.success && response.data.schedule) {
        // Guardar en localStorage para que ScheduleViewer lo pueda leer
        localStorage.setItem('generatedSchedule', JSON.stringify(response.data.schedule));
        // Redirigir a schedule-viewer
        navigate('/schedule-viewer');
      } else {
        setError('Error en la generación del horario');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al generar horario';
      setError(errorMessage);
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const selectedDataset = datasets.find(d => d.name === formData.dataset);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Generar Horario</h1>
        <p className="text-gray-600 mt-2">
          Seleccione un dataset y configure los parámetros del algoritmo genético
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      <form onSubmit={handleGenerate} className="space-y-6">
        {/* Dataset Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-600" />
            Dataset
          </h2>
          
          <div className="grid grid-cols-1 gap-3">
            {datasets.map((dataset) => (
              <label
                key={dataset.name}
                className={`flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  formData.dataset === dataset.name
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="dataset"
                  value={dataset.name}
                  checked={formData.dataset === dataset.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, dataset: e.target.value }))}
                  className="sr-only"
                />
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                  formData.dataset === dataset.name
                    ? 'border-indigo-500 bg-indigo-500'
                    : 'border-gray-300'
                }`}>
                  {formData.dataset === dataset.name && (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{dataset.name}</div>
                  <div className="text-sm text-gray-500 flex gap-4 mt-1">
                    <span className="flex items-center gap-1">
                      <BookOpen className="h-3 w-3" />
                      {dataset.stats?.classes ?? dataset.stats?.courses ?? 0} clases
                    </span>
                    <span className="flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      {dataset.stats?.rooms ?? 0} aulas
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {dataset.stats?.instructors ?? 0} instructores
                    </span>
                  </div>
                </div>
              </label>
            ))}
          </div>

          {datasets.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No hay datasets XML disponibles. Coloque archivos .xml en la carpeta raíz del proyecto.
            </div>
          )}
        </div>

        {/* AG Parameters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Parámetros del Algoritmo
          </h2>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tamaño de Población
              </label>
              <input
                type="number"
                min="10"
                max="500"
                value={formData.population_size}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  population_size: parseInt(e.target.value) || 50 
                }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">Recomendado: 50-100</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Generaciones
              </label>
              <input
                type="number"
                min="10"
                max="1000"
                value={formData.generations}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  generations: parseInt(e.target.value) || 100 
                }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">Recomendado: 100-500</p>
            </div>
          </div>
        </div>

        {/* Summary & Generate Button */}
        {selectedDataset && (
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg">{selectedDataset.name}</h3>
                <p className="text-indigo-100 text-sm mt-1">
                  {selectedDataset.stats?.classes ?? selectedDataset.stats?.courses ?? 0} clases × {selectedDataset.stats?.rooms ?? 0} aulas × 5 días × 13 bloques
                </p>
              </div>
              <button
                type="submit"
                disabled={generating || !formData.dataset}
                className={`px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                  generating
                    ? 'bg-white/20 cursor-not-allowed'
                    : 'bg-white text-indigo-600 hover:bg-indigo-50 shadow-lg'
                }`}
              >
                {generating ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    Generar Horario
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}

export default Schedules;
