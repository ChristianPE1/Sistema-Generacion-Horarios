import { useState } from 'react';
import { importXML } from '../services/api';
import type { ImportStats } from '../types';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Info,
  Building2,
  Users,
  BookOpen,
  GraduationCap,
  Clock,
  Loader2,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

function ImportXML() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [stats, setStats] = useState<ImportStats | null>(null);
  const [clearExisting, setClearExisting] = useState(true);
  const [showFormatGuide, setShowFormatGuide] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(false);
      setStats(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.xml')) {
        setFile(droppedFile);
        setError(null);
        setSuccess(false);
        setStats(null);
      } else {
        setError('Por favor, selecciona un archivo XML');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Por favor selecciona un archivo XML');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('clear_existing', clearExisting ? 'true' : 'false');

      const response = await importXML(formData);
      
      setStats(response.data.stats);
      setSuccess(true);
      setFile(null);
      
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al importar el archivo XML');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setError(null);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Importar Datos XML</h1>
        <p className="text-gray-500 mt-1">Carga un archivo XML con los datos del curso para generar horarios</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all
              ${dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'}
              ${file ? 'bg-green-50 border-green-300' : ''}
            `}
          >
            <input
              type="file"
              accept=".xml"
              onChange={handleFileChange}
              disabled={loading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            
            {file ? (
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                  <FileText className="h-8 w-8 text-green-600" />
                </div>
                <p className="font-medium text-gray-900 mb-1">{file.name}</p>
                <p className="text-sm text-gray-500 mb-3">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); removeFile(); }}
                  className="inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-700"
                >
                  <X className="h-4 w-4" /> Quitar archivo
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors
                  ${dragActive ? 'bg-indigo-100' : 'bg-gray-100'}`}>
                  <Upload className={`h-8 w-8 ${dragActive ? 'text-indigo-600' : 'text-gray-400'}`} />
                </div>
                <p className="font-medium text-gray-900 mb-1">
                  Arrastra tu archivo XML aquí
                </p>
                <p className="text-sm text-gray-500">
                  o <span className="text-indigo-600 font-medium">haz clic para seleccionar</span>
                </p>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-gray-50 rounded-lg">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={clearExisting}
                onChange={(e) => setClearExisting(e.target.checked)}
                disabled={loading}
                className="w-5 h-5 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
              />
              <div>
                <span className="font-medium text-gray-700">Limpiar datos existentes</span>
                <p className="text-sm text-gray-500">Elimina todos los datos anteriores antes de importar</p>
              </div>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !file}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Importando...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5" />
                Importar XML
              </>
            )}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="mx-6 mb-6 flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Error al importar</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && stats && (
          <div className="mx-6 mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <p className="font-medium text-green-800">¡Importación exitosa!</p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <StatBadge icon={Building2} label="Aulas" value={stats.rooms} />
              <StatBadge icon={Users} label="Instructores" value={stats.instructors} />
              <StatBadge icon={BookOpen} label="Cursos" value={stats.courses} />
              <StatBadge icon={GraduationCap} label="Clases" value={stats.classes} />
              <StatBadge icon={Clock} label="Time Slots" value={stats.time_slots} />
            </div>
          </div>
        )}
      </div>

      {/* Format Guide */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <button
          onClick={() => setShowFormatGuide(!showFormatGuide)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Info className="h-5 w-5 text-blue-600" />
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-900">Guía de formato XML</p>
              <p className="text-sm text-gray-500">Ver estructura y compatibilidad del archivo</p>
            </div>
          </div>
          {showFormatGuide ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>
        
        {showFormatGuide && (
          <div className="p-6 pt-2 border-t border-gray-100 space-y-4">
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-600">
                Este sistema es compatible con archivos XML del formato <strong>ITC-2007 / UniTime Course Timetabling</strong>, 
                utilizado comúnmente en competiciones de timetabling universitario.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700 mb-3">Estructura básica del XML:</p>
              <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
{`<?xml version="1.0" encoding="UTF-8"?>
<timetable version="2.4" nrDays="7" slotsPerDay="288">
  
  <!-- Definición de aulas -->
  <rooms>
    <room id="1" capacity="118" location="451,435"/>
    <room id="2" capacity="470" location="461,444"/>
  </rooms>
  
  <!-- Definición de clases con horarios -->
  <classes>
    <class id="1" offering="1" classLimit="105">
      <instructor id="1"/>
      <time days="0100000" start="102" length="12" pref="0"/>
      <room id="1" pref="0"/>
    </class>
  </classes>
  
  <!-- Estudiantes (opcional) -->
  <students>
    <student id="1">
      <class id="1"/>
    </student>
  </students>
  
</timetable>`}
              </pre>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">Campos requeridos:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span><code className="bg-gray-100 px-1 rounded">rooms</code> - Aulas con ID y capacidad</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span><code className="bg-gray-100 px-1 rounded">classes</code> - Clases con límite de estudiantes</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span><code className="bg-gray-100 px-1 rounded">time</code> - Slots de tiempo por clase</span>
                  </li>
                </ul>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">Formato de tiempo:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li><code className="bg-gray-100 px-1 rounded">days</code> - Días de la semana (7 bits: L-D)</li>
                  <li><code className="bg-gray-100 px-1 rounded">start</code> - Slot de inicio (5 min cada uno)</li>
                  <li><code className="bg-gray-100 px-1 rounded">length</code> - Duración en slots</li>
                </ul>
                <p className="text-xs text-gray-500 mt-2">
                  Ejemplo: <code className="bg-gray-100 px-1 rounded">days="0100100"</code> = Martes y Viernes
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                <CheckCircle2 className="h-4 w-4" /> ITC-2007 Compatible
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                <CheckCircle2 className="h-4 w-4" /> UniTime Format
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                <Info className="h-4 w-4" /> Dataset LLR soportado
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Componente para badges de estadísticas
function StatBadge({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-green-200">
      <Icon className="h-4 w-4 text-green-600" />
      <div>
        <p className="text-lg font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default ImportXML;
