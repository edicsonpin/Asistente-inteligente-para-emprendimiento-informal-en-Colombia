"""
Script de prueba para crear 10 emprendedores con 20 negocios
Usa datos reales de Colombia (paises, departamentos, ciudades ya existentes)
"""

import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session



# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config2 import get_db
from app.database.models import (
    Usuario, Emprendedor, Negocio, Pais, Departamento, Ciudad, Barrio,
    SectorNegocio, EstadoEmprendedor, EstadoNegocio, TipoDocumento, Base
)
#from nucleo.seguridad import obtener_hash_contrasena


class GeneradorDatosPrueba:
    """Generador de datos de prueba para emprendedores y negocios"""
    db = next(get_db())
    def __init__(self, db_session):
        self.bd = db_session  # Asignar la base de datos al atributo
        print("hola")
        
        self.colombia_id = None
        self.departamentos = []
        self.ciudades = []
   
        
    def cargar_ubicaciones_existentes(self):
        """Carga ubicaciones existentes de la BD"""
        print("\n" + "="*70)
        print("CARGANDO UBICACIONES EXISTENTES DE COLOMBIA")
        print("="*70)
        
        # Cargar Colombia
        colombia = self.bd.query(Pais).filter(Pais.nombre == "Colombia").first()
        if not colombia:
            print("✗ ERROR: No se encontro Colombia en la base de datos")
            print("  Por favor, ejecute primero el script SQL de ubicaciones")
            sys.exit(1)
        
        self.colombia_id = colombia.pais_id
        print(f"✓ Pais: {colombia.nombre} (ID: {colombia.pais_id})")
        
        # Cargar departamentos
        self.departamentos = self.bd.query(Departamento).filter(
            Departamento.pais_id == self.colombia_id
        ).all()
        print(f"✓ Departamentos cargados: {len(self.departamentos)}")
        
        # Cargar ciudades
        self.ciudades = self.bd.query(Ciudad).join(Departamento).filter(
            Departamento.pais_id == self.colombia_id
        ).all()
        print(f"✓ Ciudades cargadas: {len(self.ciudades)}")
        
        if len(self.ciudades) == 0:
            print("✗ ERROR: No hay ciudades en la base de datos")
            sys.exit(1)
        
        # Mostrar algunas ciudades de ejemplo
        print("\nEjemplos de ciudades disponibles:")
        for ciudad in random.sample(self.ciudades, min(5, len(self.ciudades))):
            print(f"  - {ciudad.nombre} ({ciudad.departamento.nombre})")
    
    def limpiar_datos_anteriores(self):
        """Limpia datos de prueba anteriores"""
        print("\n" + "="*70)
        print("LIMPIANDO DATOS DE PRUEBA ANTERIORES")
        print("="*70)
        
        try:
            # Eliminar negocios de prueba
            negocios_eliminados = self.bd.query(Negocio).filter(
                Negocio.nombre_comercial.like("PRUEBA_%")
            ).delete(synchronize_session=False)
            
            # Eliminar emprendedores de prueba
            emprendedores_eliminados = self.bd.query(Emprendedor).filter(
                Emprendedor.usuario_id.in_(
                    self.bd.query(Usuario.usuario_id).filter(
                        Usuario.username.like("emprendedor_prueba_%")
                    )
                )
            ).delete(synchronize_session=False)
            
            # Eliminar usuarios de prueba
            usuarios_eliminados = self.bd.query(Usuario).filter(
                Usuario.username.like("emprendedor_prueba_%")
            ).delete(synchronize_session=False)
            
            self.bd.commit()
            
            print(f"✓ Usuarios eliminados: {usuarios_eliminados}")
            print(f"✓ Emprendedores eliminados: {emprendedores_eliminados}")
            print(f"✓ Negocios eliminados: {negocios_eliminados}")
            
        except Exception as error:
            print(f"✗ Error al limpiar datos: {str(error)}")
            self.bd.rollback()
    
    def generar_usuarios(self, cantidad=10):
        """Genera usuarios para emprendedores"""
        print("\n" + "="*70)
        print(f"CREANDO {cantidad} USUARIOS")
        print("="*70)
        
        nombres = [
            "Maria Rodriguez", "Carlos Gomez", "Ana Martinez", "Luis Fernandez",
            "Sofia Garcia", "Diego Torres", "Laura Sanchez", "Juan Ramirez",
            "Valentina Lopez", "Andres Diaz"
        ]
        
        usuarios_creados = []
        
        for i in range(cantidad):
            usuario = Usuario(
                username=f"emprendedor_prueba_{i+1:03d}",
                password_hash=obtener_hash_contrasena("Password123!"),
                email=f"emprendedor_prueba_{i+1:03d}@test.com",
                nombre_completo=nombres[i] if i < len(nombres) else f"Emprendedor {i+1}",
                tipo_usuario="EMPRENDEDOR",
                telefono=f"300{random.randint(1000000, 9999999)}",
                estado="ACTIVO"
            )
            
            self.bd.add(usuario)
            usuarios_creados.append(usuario)
        
        self.bd.commit()
        
        for usuario in usuarios_creados:
            self.bd.refresh(usuario)
        
        print(f"✓ {len(usuarios_creados)} usuarios creados exitosamente")
        return usuarios_creados
    
    def generar_emprendedores(self, usuarios):
        """Genera emprendedores basados en usuarios"""
        print("\n" + "="*70)
        print(f"CREANDO {len(usuarios)} EMPRENDEDORES")
        print("="*70)
        
        habilidades_pool = [
            ["Python", "Django", "FastAPI", "PostgreSQL"],
            ["JavaScript", "React", "Node.js", "MongoDB"],
            ["Java", "Spring Boot", "MySQL", "Docker"],
            ["Gestion Empresarial", "Marketing Digital", "Ventas"],
            ["Contabilidad", "Finanzas", "Excel Avanzado"],
            ["Diseño Grafico", "Adobe Suite", "UI/UX"],
            ["Desarrollo Movil", "Flutter", "React Native"],
            ["Data Science", "Machine Learning", "Python"],
            ["Ingles Avanzado", "Atencion al Cliente", "CRM"],
            ["Logistica", "Cadena de Suministro", "Inventarios"]
        ]
        
        intereses_pool = [
            ["Tecnologia", "Innovacion", "Startups"],
            ["Comercio Electronico", "Retail", "Ventas Online"],
            ["Educacion", "Capacitacion", "E-learning"],
            ["Salud", "Bienestar", "Fitness"],
            ["Gastronomia", "Restaurantes", "Catering"],
            ["Turismo", "Hospedaje", "Experiencias"],
            ["Manufactura", "Produccion", "Industria"],
            ["Agricultura", "Agroecologia", "Sostenibilidad"],
            ["Construccion", "Arquitectura", "Ingenieria"],
            ["Servicios Profesionales", "Consultoria", "Asesoria"]
        ]
        
        idiomas_pool = [
            ["Espanol"],
            ["Espanol", "Ingles"],
            ["Espanol", "Ingles", "Frances"],
            ["Espanol", "Ingles", "Portugues"],
            ["Espanol", "Italiano"]
        ]
        
        emprendedores_creados = []
        
        for idx, usuario in enumerate(usuarios):
            # Seleccionar ciudad aleatoria
            ciudad = random.choice(self.ciudades)
            departamento = ciudad.departamento
            
            emprendedor = Emprendedor(
                usuario_id=usuario.usuario_id,
                biografia=f"Emprendedor con experiencia en diversos sectores, basado en {ciudad.nombre}",
                experiencia_total=random.randint(24, 180),  # 2 a 15 años
                habilidades=habilidades_pool[idx % len(habilidades_pool)],
                intereses=intereses_pool[idx % len(intereses_pool)],
                linkedin_url=f"https://linkedin.com/in/{usuario.username}",
                sitio_web_personal=f"https://{usuario.username}.com",
                pais_residencia_id=self.colombia_id,
                departamento_residencia_id=departamento.departamento_id,
                ciudad_residencia_id=ciudad.ciudad_id,
                direccion_residencia=f"Calle {random.randint(1, 200)} No. {random.randint(1, 99)}-{random.randint(1, 99)}",
                preferencia_contacto="EMAIL",
                recibir_notificaciones=True,
                idiomas=random.choice(idiomas_pool),
                estado="ACTIVO"
            )
            
            self.bd.add(emprendedor)
            emprendedores_creados.append(emprendedor)
        
        self.bd.commit()
        
        for emprendedor in emprendedores_creados:
            self.bd.refresh(emprendedor)
        
        print(f"✓ {len(emprendedores_creados)} emprendedores creados exitosamente")
        
        # Mostrar resumen
        print("\nResumen de emprendedores creados:")
        for emp in emprendedores_creados[:5]:  # Mostrar primeros 5
            print(f"  - {emp.usuario.nombre_completo} en {emp.ciudad_residencia.nombre}")
        
        return emprendedores_creados
    
    def generar_negocios(self, emprendedores, cantidad_total=20):
        """Genera negocios para los emprendedores"""
        print("\n" + "="*70)
        print(f"CREANDO {cantidad_total} NEGOCIOS")
        print("="*70)
        
        sectores = [
            "TECNOLOGIA", "COMERCIO", "SERVICIOS", "INDUSTRIA", 
            "AGRICULTURA", "CONSTRUCCION", "TURISMO", "EDUCACION"
        ]
        
        nombres_comerciales = [
            "TechSolutions", "DataAnalytics", "WebDev Pro", "AppMakers",
            "Comercial La Esquina", "Tienda Digital", "SuperMercado Express",
            "Consultores Asociados", "Servicios Integrales", "Asesoria Legal",
            "Fabrica de Calzado", "Textiles del Valle", "Industrias Unidas",
            "Agro Campo Verde", "Cultivos Organicos", "Finca La Esperanza",
            "Constructora El Futuro", "Ingenieria y Obras", "Proyectos Civiles",
            "Hotel Boutique", "Tours y Aventuras", "Catering Gourmet"
        ]
        
        descripciones = {
            "TECNOLOGIA": "Desarrollo de soluciones tecnologicas innovadoras",
            "COMERCIO": "Comercializacion de productos de alta calidad",
            "SERVICIOS": "Prestacion de servicios profesionales especializados",
            "INDUSTRIA": "Manufactura y produccion industrial",
            "AGRICULTURA": "Produccion agricola sostenible",
            "CONSTRUCCION": "Construccion y obras de ingenieria",
            "TURISMO": "Servicios turisticos y hoteleros",
            "EDUCACION": "Servicios educativos y de capacitacion"
        }
        
        negocios_creados = []
        nombres_usados = set()
        
        for i in range(cantidad_total):
            # Seleccionar emprendedor (permitir múltiples negocios)
            emprendedor = random.choice(emprendedores)
            
            # Generar nombre único
            while True:
                nombre_base = random.choice(nombres_comerciales)
                nombre_comercial = f"PRUEBA_{nombre_base} {random.randint(100, 999)}"
                if nombre_comercial not in nombres_usados:
                    nombres_usados.add(nombre_comercial)
                    break
            
            # Seleccionar ubicación
            ciudad = random.choice(self.ciudades)
            departamento = ciudad.departamento
            
            # Seleccionar sector
            sector = random.choice(sectores)
            
            # Generar datos financieros realistas
            ingresos_mensuales = random.choice([
                random.uniform(2000000, 5000000),    # Micro
                random.uniform(5000000, 15000000),   # Pequeña
                random.uniform(15000000, 40000000)   # Mediana
            ])
            
            # Determinar si es negocio principal (primero de cada emprendedor)
            es_principal = len([n for n in negocios_creados if n.emprendedor_id == emprendedor.id]) == 0
            
            # Calcular meses de operación
            meses_operacion = random.randint(6, 60)  # 6 meses a 5 años
            
            negocio = Negocio(
                emprendedor_id=emprendedor.id,
                nombre_comercial=nombre_comercial,
                razon_social=f"{nombre_base} SAS" if random.random() > 0.5 else f"{nombre_base} Ltda",
                es_mipyme=True,
                es_negocio_principal=es_principal,
                tipo_documento=random.choice(["NIT", "RUT", "CEDULA"]),
                numero_documento=f"900{random.randint(100000, 999999)}-{random.randint(1, 9)}",
                fecha_constitucion=datetime.now() - timedelta(days=meses_operacion*30),
                camara_comercio=f"Camara de Comercio de {ciudad.nombre}",
                sector_negocio=sector,
                subsector=f"Subsector {sector}",
                codigo_ciiu=f"{random.randint(1000, 9999)}",
                descripcion_actividad=descripciones[sector],
                experiencia_sector=random.randint(12, 72),
                meses_operacion=meses_operacion,
                empleados_directos=random.randint(1, 15),
                empleados_indirectos=random.randint(0, 5),
                modelo_negocio=random.choice(["B2B", "B2C", "B2B2C", "Marketplace", "SaaS"]),
                sitio_web=f"https://{nombre_comercial.lower().replace(' ', '')}.com",
                ingresos_mensuales_promedio=ingresos_mensuales,
                ingresos_anuales=ingresos_mensuales * 12,
                capital_trabajo=ingresos_mensuales * random.uniform(1.5, 3.0),
                deuda_existente=ingresos_mensuales * random.uniform(0, 0.5),
                activos_totales=ingresos_mensuales * random.uniform(3, 6),
                pasivos_totales=ingresos_mensuales * random.uniform(0.5, 2),
                flujo_efectivo_mensual=ingresos_mensuales * random.uniform(0.2, 0.4),
                puntaje_credito_negocio=random.randint(600, 850),
                historial_pagos_negocio=random.randint(70, 100),
                calificacion_riesgo_negocio=random.choice(["MUY_BAJO", "BAJO", "MEDIO", "ALTO"]),
                pais_id=self.colombia_id,
                departamento_id=departamento.departamento_id,
                ciudad_id=ciudad.ciudad_id,
                direccion_comercial=f"Carrera {random.randint(1, 100)} No. {random.randint(1, 99)}-{random.randint(1, 99)}",
                coordenadas_gps={"latitud": float(ciudad.latitud), "longitud": float(ciudad.longitud)},
                telefono_comercial=f"60{random.randint(1, 9)}{random.randint(1000000, 9999999)}",
                email_comercial=f"contacto@{nombre_comercial.lower().replace(' ', '')}.com",
                persona_contacto=emprendedor.usuario.nombre_completo,
                estado="ACTIVO",
                edad_negocio=int(meses_operacion / 12),
                ratio_deuda_ingresos=random.uniform(0.0, 0.3),
                rentabilidad_estimada=random.uniform(0.1, 0.4)
            )
            
            self.bd.add(negocio)
            negocios_creados.append(negocio)
        
        self.bd.commit()
        
        for negocio in negocios_creados:
            self.bd.refresh(negocio)
        
        print(f"✓ {len(negocios_creados)} negocios creados exitosamente")
        
        return negocios_creados
    
    def generar_estadisticas(self, emprendedores, negocios):
        """Genera estadísticas de los datos creados"""
        print("\n" + "="*70)
        print("ESTADISTICAS DE DATOS GENERADOS")
        print("="*70)
        
        # Estadísticas de emprendedores
        print("\n📊 EMPRENDEDORES:")
        print(f"  Total: {len(emprendedores)}")
        
        ciudades_emp = {}
        for emp in emprendedores:
            ciudad_nombre = emp.ciudad_residencia.nombre
            ciudades_emp[ciudad_nombre] = ciudades_emp.get(ciudad_nombre, 0) + 1
        
        print("\n  Distribución por ciudad:")
        for ciudad, cantidad in sorted(ciudades_emp.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {ciudad}: {cantidad}")
        
        # Estadísticas de negocios
        print("\n📊 NEGOCIOS:")
        print(f"  Total: {len(negocios)}")
        
        sectores_count = {}
        for neg in negocios:
            sector = neg.sector_negocio
            sectores_count[sector] = sectores_count.get(sector, 0) + 1
        
        print("\n  Distribución por sector:")
        for sector, cantidad in sorted(sectores_count.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {sector}: {cantidad}")
        
        # Negocios por emprendedor
        negocios_por_emp = {}
        for neg in negocios:
            emp_id = neg.emprendedor_id
            negocios_por_emp[emp_id] = negocios_por_emp.get(emp_id, 0) + 1
        
        print("\n  Distribución de negocios por emprendedor:")
        for emp_id, cantidad in sorted(negocios_por_emp.items(), key=lambda x: x[1], reverse=True)[:5]:
            emp = next(e for e in emprendedores if e.id == emp_id)
            print(f"    - {emp.usuario.nombre_completo}: {cantidad} negocio(s)")
        
        # Estadísticas financieras
        ingresos_totales = sum(n.ingresos_mensuales_promedio for n in negocios)
        ingresos_promedio = ingresos_totales / len(negocios)
        empleados_totales = sum(n.empleados_directos for n in negocios)
        
        print("\n  Indicadores financieros:")
        print(f"    - Ingresos mensuales totales: ${ingresos_totales:,.0f} COP")
        print(f"    - Ingreso promedio por negocio: ${ingresos_promedio:,.0f} COP")
        print(f"    - Total empleados directos: {empleados_totales}")
        print(f"    - Promedio empleados por negocio: {empleados_totales/len(negocios):.1f}")
        
        # Ciudades con más negocios
        ciudades_neg = {}
        for neg in negocios:
            ciudad_nombre = neg.ciudad.nombre
            ciudades_neg[ciudad_nombre] = ciudades_neg.get(ciudad_nombre, 0) + 1
        
        print("\n  Top 5 ciudades con más negocios:")
        for ciudad, cantidad in sorted(ciudades_neg.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {ciudad}: {cantidad}")
    
    def mostrar_ejemplos(self, emprendedores, negocios):
        """Muestra ejemplos detallados de los datos creados"""
        print("\n" + "="*70)
        print("EJEMPLOS DE DATOS CREADOS")
        print("="*70)
        
        # Ejemplo de emprendedor
        emp_ejemplo = emprendedores[0]
        print("\n🧑 EJEMPLO DE EMPRENDEDOR:")
        print(f"  ID: {emp_ejemplo.id}")
        print(f"  Nombre: {emp_ejemplo.usuario.nombre_completo}")
        print(f"  Username: {emp_ejemplo.usuario.username}")
        print(f"  Email: {emp_ejemplo.usuario.email}")
        print(f"  Experiencia: {emp_ejemplo.experiencia_total} meses")
        print(f"  Habilidades: {', '.join(emp_ejemplo.habilidades)}")
        print(f"  Ubicacion: {emp_ejemplo.ciudad_residencia.nombre}, {emp_ejemplo.departamento_residencia.nombre}")
        
        # Ejemplo de negocio
        neg_ejemplo = negocios[0]
        print("\n🏢 EJEMPLO DE NEGOCIO:")
        print(f"  ID: {neg_ejemplo.id}")
        print(f"  Nombre: {neg_ejemplo.nombre_comercial}")
        print(f"  Sector: {neg_ejemplo.sector_negocio}")
        print(f"  Propietario: {neg_ejemplo.emprendedor.usuario.nombre_completo}")
        print(f"  Ubicacion: {neg_ejemplo.ciudad.nombre}, {neg_ejemplo.departamento.nombre}")
        print(f"  Empleados: {neg_ejemplo.empleados_directos} directos, {neg_ejemplo.empleados_indirectos} indirectos")
        print(f"  Ingresos mensuales: ${neg_ejemplo.ingresos_mensuales_promedio:,.0f} COP")
        print(f"  Meses operacion: {neg_ejemplo.meses_operacion}")
        print(f"  Calificacion riesgo: {neg_ejemplo.calificacion_riesgo_negocio}")
    
    def generar_credenciales(self):
        """Muestra las credenciales de acceso"""
        print("\n" + "="*70)
        print("CREDENCIALES DE ACCESO")
        print("="*70)
        print("\nTodos los usuarios tienen la misma contraseña: Password123!")
        print("\nEjemplos de usuarios creados:")
        for i in range(1, 6):
            print(f"  Username: emprendedor_prueba_{i:03d}")
            print(f"  Password: Password123!")
            print(f"  Email: emprendedor_prueba_{i:03d}@test.com")
            print()
    
    def ejecutar_generacion_completa(self):
        """Ejecuta el proceso completo de generación de datos"""
        print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  GENERADOR DE DATOS DE PRUEBA                                    ║
    ║  10 Emprendedores + 20 Negocios                                  ║
    ║  Usando ubicaciones reales de Colombia                           ║
    ╚══════════════════════════════════════════════════════════════════╝
        """)
        
        try:
            # 1. Cargar ubicaciones
            self.cargar_ubicaciones_existentes()
            
            # 2. Limpiar datos anteriores
            self.limpiar_datos_anteriores()
            
            # 3. Generar usuarios
            usuarios = self.generar_usuarios(10)
            
            # 4. Generar emprendedores
            emprendedores = self.generar_emprendedores(usuarios)
            
            # 5. Generar negocios
            negocios = self.generar_negocios(emprendedores, 20)
            
            # 6. Mostrar estadísticas
            self.generar_estadisticas(emprendedores, negocios)
            
            # 7. Mostrar ejemplos
            self.mostrar_ejemplos(emprendedores, negocios)
            
            # 8. Mostrar credenciales
            self.generar_credenciales()
            
            print("\n" + "="*70)
            print("✓ GENERACION COMPLETADA EXITOSAMENTE")
            print("="*70)
            
        except Exception as error:
            print(f"\n✗ ERROR DURANTE LA GENERACION: {str(error)}")
            import traceback
            traceback.print_exc()
            self.bd.rollback()
        finally:
            self.bd.close()


if __name__ == "__main__":
    if __name__ == "__main__":
     db_session = next(get_db())  # Obtener la sesión de la base de datos
     generador = GeneradorDatosPrueba(db_session)  # Pasar la sesión al generador
     generador.ejecutar_generacion_completa()