"""
Generador de horarios directo desde archivos JSON/XML sin cargar a base de datos.
Optimizado para velocidad y para despliegue con archivos en bucket.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import numpy as np


@dataclass
class RoomData:
    """Datos de una sala"""
    id: str
    capacidad: int
    tipo: str = 'normal'  # 'normal', 'lab', 'auditorio'


@dataclass
class ProfesorData:
    """Datos de un profesor"""
    id: str
    nombre: str
    max_horas_diarias: int = 8
    disponibilidad: Dict = None


@dataclass
class CursoData:
    """Datos de un curso"""
    codigo: str
    nombre: str
    anio: int
    horas_teoria: int
    horas_practica: int
    horas_lab: int
    profesor_id: str
    num_estudiantes: int
    requiere_lab: int


@dataclass
class TimeSlotData:
    """Slot de tiempo para una clase"""
    dias: str  # Patrón de días (ej: '1010100' para Lun-Mie-Vie)
    hora_inicio: int  # Slot de inicio (5 min por slot)
    duracion: int  # Duración en slots
    num_bloques: int  # Número de bloques de 50 min
    duracion_bloque_min: int = 50  # Duración de cada bloque


@dataclass
class AsignacionData:
    """Asignación de clase-sala-tiempo"""
    curso_codigo: str
    sala_id: str
    time_slot: TimeSlotData
    profesor_id: str


class DirectScheduleGenerator:
    """
    Generador de horarios directo desde archivos JSON/XML.
    No requiere cargar datos a base de datos.
    """
    
    def __init__(self, config: Dict = None):
        """
        Args:
            config: Configuración del generador
        """
        self.config = config or {}
        self.salas: List[RoomData] = []
        self.profesores: List[ProfesorData] = []
        self.cursos: List[CursoData] = []
        
        # Configuración de bloques
        self.duracion_bloque_min = self.config.get('duracion_bloque_min', 50)
        self.max_bloques_consecutivos = self.config.get('max_bloques_consecutivos_por_sesion', 3)
        self.descanso_entre_bloques_min = self.config.get('descanso_entre_bloques_min', 10)
        self.inicio_jornada = self.config.get('inicio_jornada', '07:00')
        self.fin_jornada = self.config.get('fin_jornada', '20:10')
        
    def load_from_json(self, json_path: str):
        """
        Carga datos desde archivo JSON
        
        Args:
            json_path: Ruta al archivo JSON
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cargar salas
        self.salas = [
            RoomData(
                id=sala['id'],
                capacidad=sala['capacidad'],
                tipo=sala.get('tipo', 'normal')
            )
            for sala in data.get('salas', [])
        ]
        
        # Cargar profesores
        self.profesores = [
            ProfesorData(
                id=prof['id'],
                nombre=prof['nombre'],
                max_horas_diarias=prof.get('max_horas_diarias', 8),
                disponibilidad=prof.get('disponibilidad', {})
            )
            for prof in data.get('profesores', [])
        ]
        
        # Cargar cursos
        self.cursos = [
            CursoData(
                codigo=curso['codigo'],
                nombre=curso['nombre'],
                anio=curso['anio'],
                horas_teoria=curso['horas_teoria'],
                horas_practica=curso['horas_practica'],
                horas_lab=curso['horas_lab'],
                profesor_id=curso['profesor_id'],
                num_estudiantes=curso['num_estudiantes'],
                requiere_lab=curso['requiere_lab']
            )
            for curso in data.get('cursos', [])
        ]
        
        # Actualizar config si viene en el JSON
        if 'configuracion_general' in data:
            self.config.update(data['configuracion_general'])
            self.duracion_bloque_min = self.config.get('duracion_bloque_min', 50)
            self.max_bloques_consecutivos = self.config.get('max_bloques_consecutivos_por_sesion', 3)
            self.descanso_entre_bloques_min = self.config.get('descanso_entre_bloques_min', 10)
            self.inicio_jornada = self.config.get('inicio_jornada', '07:00')
            self.fin_jornada = self.config.get('fin_jornada', '20:10')
    
    def load_from_xml(self, xml_path: str):
        """
        Carga datos desde archivo XML (formato Purdue)
        
        Args:
            xml_path: Ruta al archivo XML
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Cargar salas
        rooms_elem = root.find('rooms')
        if rooms_elem is not None:
            for room_elem in rooms_elem.findall('room'):
                self.salas.append(RoomData(
                    id=room_elem.get('id'),
                    capacidad=int(room_elem.get('capacity', 30)),
                    tipo='normal'
                ))
        
        # Cargar instructores
        instructors_elem = root.find('instructors')
        if instructors_elem is not None:
            for instructor_elem in instructors_elem.findall('instructor'):
                self.profesores.append(ProfesorData(
                    id=instructor_elem.get('id'),
                    nombre=instructor_elem.get('name', f"Instructor {instructor_elem.get('id')}"),
                    max_horas_diarias=8,
                    disponibilidad={}
                ))
        
        # Cargar cursos desde clases
        classes_elem = root.find('classes')
        if classes_elem is not None:
            for class_elem in classes_elem.findall('class'):
                # Extraer información del curso
                course_elem = class_elem.find('course')
                instructor_elem = class_elem.find('instructor')
                
                # Calcular horas desde time slots
                time_slots = class_elem.findall('time')
                total_horas = 0
                
                if time_slots:
                    # Usar el primer time slot como referencia
                    first_time = time_slots[0]
                    length = int(first_time.get('length', 12))  # En slots de 5 min
                    total_horas = (length * 5) // 60  # Convertir a horas
                
                self.cursos.append(CursoData(
                    codigo=course_elem.get('code', f"C{class_elem.get('id')}") if course_elem is not None else f"C{class_elem.get('id')}",
                    nombre=course_elem.get('name', f"Curso {class_elem.get('id')}") if course_elem is not None else f"Curso {class_elem.get('id')}",
                    anio=1,
                    horas_teoria=total_horas // 2,
                    horas_practica=total_horas // 2,
                    horas_lab=0,
                    profesor_id=instructor_elem.get('id') if instructor_elem is not None else 'P000',
                    num_estudiantes=int(class_elem.get('classLimit', 30)),
                    requiere_lab=0
                ))
    
    def time_to_slot(self, time_str: str) -> int:
        """Convierte HH:MM a número de slot (5 min por slot)"""
        inicio = datetime.strptime(self.inicio_jornada, '%H:%M')
        tiempo = datetime.strptime(time_str, '%H:%M')
        diff_minutes = int((tiempo - inicio).total_seconds() / 60)
        return diff_minutes // 5
    
    def slot_to_time(self, slot: int) -> str:
        """Convierte número de slot a HH:MM"""
        inicio = datetime.strptime(self.inicio_jornada, '%H:%M')
        tiempo = inicio + timedelta(minutes=slot * 5)
        return tiempo.strftime('%H:%M')
    
    def generate_time_slots_for_curso(self, curso: CursoData) -> List[TimeSlotData]:
        """
        Genera posibles time slots para un curso respetando bloques de 50 min
        
        Args:
            curso: Datos del curso
            
        Returns:
            Lista de posibles time slots
        """
        slots = []
        
        # Calcular total de horas semanales
        total_horas = curso.horas_teoria + curso.horas_practica + curso.horas_lab
        
        # Convertir horas a bloques (1 hora ≈ 1 bloque de 50 min)
        bloques_necesarios = int(total_horas)
        
        # Distribuir en sesiones respetando máximo de bloques consecutivos
        sesiones = []
        bloques_restantes = bloques_necesarios
        
        while bloques_restantes > 0:
            bloques_en_sesion = min(bloques_restantes, self.max_bloques_consecutivos)
            sesiones.append(bloques_en_sesion)
            bloques_restantes -= bloques_en_sesion
        
        # Patrones de días comunes
        dias_patterns = [
            '1010100',  # Lun-Mie-Vie
            '0101010',  # Mar-Jue-Sab
            '1111100',  # Lun-Vie
            '1100000',  # Lun-Mar
            '0011000',  # Mie-Jue
        ]
        
        # Horarios de inicio (cada 2 horas)
        inicio_dt = datetime.strptime(self.inicio_jornada, '%H:%M')
        fin_dt = datetime.strptime(self.fin_jornada, '%H:%M')
        
        horarios_inicio = []
        current_time = inicio_dt
        while current_time < fin_dt:
            horarios_inicio.append(current_time.strftime('%H:%M'))
            current_time += timedelta(hours=2)
        
        # Generar slots
        for dias in dias_patterns:
            for hora_inicio in horarios_inicio:
                for num_bloques in sesiones:
                    # Duración total: (bloques * 50) + (bloques-1) * descanso
                    duracion_total_min = (num_bloques * self.duracion_bloque_min) + \
                                        ((num_bloques - 1) * self.descanso_entre_bloques_min)
                    
                    duracion_slots = duracion_total_min // 5
                    
                    slot = TimeSlotData(
                        dias=dias,
                        hora_inicio=self.time_to_slot(hora_inicio),
                        duracion=duracion_slots,
                        num_bloques=num_bloques,
                        duracion_bloque_min=self.duracion_bloque_min
                    )
                    
                    slots.append(slot)
        
        return slots
    
    def generate_schedule_simple(self) -> Tuple[List[AsignacionData], Dict]:
        """
        Genera horario con reglas:
        - No cruces de horario
        - Máximo 3 sesiones consecutivas del mismo curso
        - 10 min break entre cursos diferentes
        - Laboratorios no cuentan como sesiones consecutivas
        
        Returns:
            Tupla (asignaciones, estadísticas)
        """
        asignaciones = []
        stats = {
            'cursos_asignados': 0,
            'cursos_totales': len(self.cursos),
            'conflictos': 0,
            'tiempo_ms': 0
        }
        
        start_time = datetime.now()
        
        # Rastrear ocupación
        sala_ocupada = {}  # {(sala_id, slot_inicio, slot_fin, dia): curso_codigo}
        profesor_ocupado = {}  # {(profesor_id, slot_inicio, slot_fin, dia): curso_codigo}
        
        # Rastrear sesiones consecutivas del mismo curso por día
        # {(dia, hora_fin): (curso_codigo, num_sesiones_consecutivas, es_lab)}
        sesiones_consecutivas = {}
        
        # Ordenar cursos por estudiantes
        cursos_ordenados = sorted(self.cursos, key=lambda c: c.num_estudiantes, reverse=True)
        
        for curso in cursos_ordenados:
            # Filtrar salas
            salas_validas = [s for s in self.salas if s.capacidad >= curso.num_estudiantes]
            
            if curso.requiere_lab > 0:
                salas_validas = [s for s in salas_validas if s.tipo == 'lab']
            
            if not salas_validas:
                salas_validas = self.salas
            
            # Generar time slots
            time_slots = self.generate_time_slots_for_curso(curso)
            
            asignado = False
            
            for sala in salas_validas:
                if asignado:
                    break
                    
                for ts in time_slots:
                    conflicto = False
                    es_lab = curso.requiere_lab > 0
                    
                    # Verificar conflictos en cada día
                    for dia_idx, dia_activo in enumerate(ts.dias):
                        if dia_activo == '1':
                            # Conflicto de sala
                            for slot in range(ts.hora_inicio, ts.hora_inicio + ts.duracion):
                                key_sala = (sala.id, slot, dia_idx)
                                if key_sala in sala_ocupada:
                                    conflicto = True
                                    break
                            
                            if conflicto:
                                break
                            
                            # Conflicto de profesor
                            for slot in range(ts.hora_inicio, ts.hora_inicio + ts.duracion):
                                key_prof = (curso.profesor_id, slot, dia_idx)
                                if key_prof in profesor_ocupado:
                                    conflicto = True
                                    break
                            
                            if conflicto:
                                break
                            
                            # Verificar regla de 3 sesiones consecutivas
                            # Buscar si hay sesión justo antes (sin break de 10 min)
                            break_slots = 2  # 10 min = 2 slots de 5 min
                            hora_anterior = ts.hora_inicio - break_slots
                            
                            key_anterior = (dia_idx, hora_anterior)
                            if key_anterior in sesiones_consecutivas:
                                curso_ant, num_consecutivas, lab_ant = sesiones_consecutivas[key_anterior]
                                
                                # Si es el mismo curso y no es lab
                                if curso_ant == curso.codigo and not es_lab and not lab_ant:
                                    if num_consecutivas >= self.max_bloques_consecutivos:
                                        conflicto = True
                                        break
                    
                    if not conflicto:
                        # Asignar
                        asignaciones.append(AsignacionData(
                            curso_codigo=curso.codigo,
                            sala_id=sala.id,
                            time_slot=ts,
                            profesor_id=curso.profesor_id
                        ))
                        
                        # Marcar ocupación
                        for dia_idx, dia_activo in enumerate(ts.dias):
                            if dia_activo == '1':
                                for slot in range(ts.hora_inicio, ts.hora_inicio + ts.duracion):
                                    sala_ocupada[(sala.id, slot, dia_idx)] = curso.codigo
                                    profesor_ocupado[(curso.profesor_id, slot, dia_idx)] = curso.codigo
                                
                                # Actualizar sesiones consecutivas
                                break_slots = 2
                                hora_anterior = ts.hora_inicio - break_slots
                                key_anterior = (dia_idx, hora_anterior)
                                
                                # Determinar número de sesiones consecutivas
                                num_consecutivas = 1
                                if key_anterior in sesiones_consecutivas:
                                    curso_ant, num_ant, lab_ant = sesiones_consecutivas[key_anterior]
                                    if curso_ant == curso.codigo and not es_lab and not lab_ant:
                                        num_consecutivas = num_ant + 1
                                
                                # Registrar esta sesión
                                hora_fin = ts.hora_inicio + ts.duracion
                                sesiones_consecutivas[(dia_idx, hora_fin)] = (curso.codigo, num_consecutivas, es_lab)
                        
                        stats['cursos_asignados'] += 1
                        asignado = True
                        break
        
        end_time = datetime.now()
        stats['tiempo_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return asignaciones, stats
    
    def export_to_json(self, asignaciones: List[AsignacionData], output_path: str):
        """
        Exporta asignaciones a JSON
        
        Args:
            asignaciones: Lista de asignaciones
            output_path: Ruta del archivo de salida
        """
        dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        result = {
            'generado': datetime.now().isoformat(),
            'asignaciones': []
        }
        
        for asig in asignaciones:
            # Convertir patrón de días a lista de nombres
            dias = [dias_nombre[i] for i, d in enumerate(asig.time_slot.dias) if d == '1']
            
            result['asignaciones'].append({
                'curso_codigo': asig.curso_codigo,
                'sala_id': asig.sala_id,
                'profesor_id': asig.profesor_id,
                'dias': dias,
                'hora_inicio': self.slot_to_time(asig.time_slot.hora_inicio),
                'duracion_minutos': asig.time_slot.duracion * 5,
                'num_bloques': asig.time_slot.num_bloques,
                'duracion_bloque_min': asig.time_slot.duracion_bloque_min
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


def generate_from_json_file(json_path: str, output_path: str = None) -> Tuple[List[AsignacionData], Dict]:
    """
    Genera horario directamente desde archivo JSON sin usar BD
    
    Args:
        json_path: Ruta al archivo JSON con los datos
        output_path: Ruta para guardar el resultado (opcional)
        
    Returns:
        Tupla (asignaciones, estadísticas)
    """
    generator = DirectScheduleGenerator()
    generator.load_from_json(json_path)
    asignaciones, stats = generator.generate_schedule_simple()
    
    if output_path:
        generator.export_to_json(asignaciones, output_path)
    
    return asignaciones, stats


def generate_from_xml_file(xml_path: str, output_path: str = None) -> Tuple[List[AsignacionData], Dict]:
    """
    Genera horario directamente desde archivo XML sin usar BD
    
    Args:
        xml_path: Ruta al archivo XML con los datos
        output_path: Ruta para guardar el resultado (opcional)
        
    Returns:
        Tupla (asignaciones, estadísticas)
    """
    generator = DirectScheduleGenerator()
    generator.load_from_xml(xml_path)
    asignaciones, stats = generator.generate_schedule_simple()
    
    if output_path:
        generator.export_to_json(asignaciones, output_path)
    
    return asignaciones, stats


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python direct_generator.py <archivo_json_o_xml> [archivo_salida]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_schedule.json').replace('.xml', '_schedule.json')
    
    if input_file.endswith('.json'):
        asignaciones, stats = generate_from_json_file(input_file, output_file)
    elif input_file.endswith('.xml'):
        asignaciones, stats = generate_from_xml_file(input_file, output_file)
    else:
        print("Error: El archivo debe ser .json o .xml")
        sys.exit(1)
    
    print(f"\n=== Resultado de Generación ===")
    print(f"Cursos asignados: {stats['cursos_asignados']} / {stats['cursos_totales']}")
    print(f"Tiempo: {stats['tiempo_ms']} ms")
    print(f"Resultado guardado en: {output_file}")
