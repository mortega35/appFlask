from datetime import datetime

from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = 'admin123'

from models import Preceptor, Asistencia, padre, Estudiante, Curso
from models import db
import hashlib



@app.route('/')
def index():
    if not session.get("name"):
        return redirect("/login")
    return render_template('index.html')

#formulario de inicio de sesion
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("email")
        usuario_actual = Preceptor.query.filter_by(correo=session["name"]).first()
        usuario_padre = padre.query.filter_by(correo=session["name"]).first()
        if usuario_actual is None and usuario_padre is None:
            return render_template('error2.html')
        elif usuario_actual != None:
            clave = usuario_actual.clave
            verificacion = request.form['password']
            result = hashlib.md5(bytes(verificacion, encoding='utf-8'))
            if result.hexdigest() == clave:
                return redirect("/opciones")
            else:
                return render_template("error.html")
        else:
            clave = usuario_padre.clave
            verificacion = request.form['password']
            result = hashlib.md5(bytes(verificacion, encoding='utf-8'))
            if result.hexdigest() == clave:
                return redirect('/consultar_inasistencias')
            else:
                return render_template("error.html")
    else:
        return render_template('login.html')

#cerrar sesion del usuario
@app.route('/logout')
def logout():
    session["name"] = None
    return redirect("/")

#opciones del precetor
@app.route('/opciones',methods = ['POST','GET'])
def opciones():
    if request.method == 'POST':
        opcion = request.form['opcion']
        if opcion == 'registrar':
            preceptor = Preceptor.query.filter_by(correo=session['name']).first() #de esta manera trae el preceptor
            session['id'] = preceptor.id
            #cursos = Curso.query.filter_by(idpreceptor=preceptor.id) # de esta manera trae un iterable con todos los cursos que tenga el id del preceptor
            cursos = preceptor.curso
            return render_template('registrarasistencia.html', cursos=cursos)
        elif request.form['opcion'] == 'informe':
            preceptor = Preceptor.query.filter_by(correo=session['name']).first()  # de esta manera trae el preceptor
            session['id'] = preceptor.id
            cursos = Curso.query.filter_by(idpreceptor=preceptor.id)
            return render_template('informe_detalles.html', cursos=cursos)
        else:
            preceptor = Preceptor.query.filter_by(correo=session['name']).first()  # de esta manera trae el preceptor
            session['id'] = preceptor.id
            cursos = Curso.query.filter_by(idpreceptor=preceptor.id)
            return render_template('listado_asistencia.html', cursos=cursos)
    else:
        return render_template('opciones.html')

#opcion registrar asistencia
@app.route('/registrar_asistencia', methods=["POST", "GET"])
def registrar_asistencia():
    if request.method == 'POST':
        curso = int(request.form['curso'])

        clase = int(request.form['clase'])

        fecha_str = request.form['fecha']
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        if not curso and not clase and not fecha:
            return "Por favor, complete todos los campos requeridos"
        else:
            if type(curso) == int and type(clase) == int and type(fecha) == datetime:
                session['clase'] = clase
                session['fecha'] = fecha
                session['curso'] = curso
                curso_est = Curso.query.filter_by(anio=curso, idpreceptor=session['id']).first()
                estudiantes = Estudiante.query.filter_by(idcurso=curso_est.id).order_by(Estudiante.apellido).all()
                session['cursoid'] = curso_est.id
                return render_template("listar_estudiantes.html", estudiantes=estudiantes)
            else:
                return "tipo de campos erroneos, no int o  no datetime"

    else:
        return render_template('registrarasistencia.html')


@app.route("/listar_estudiantes", methods=["POST","GET"])
def listar_estudiantes():
    if request.method == 'POST':
        estudiantes = Estudiante.query.filter_by(idcurso=session['cursoid']).order_by(Estudiante.apellido).all()
        datos_formulario = request.form
        for estudiante in estudiantes:
            idestudiante= estudiante.id
            asistencia = datos_formulario.get(str(estudiante.id))
            nueva_asistencia = Asistencia(fecha=session['fecha'],codigoclase=session['clase'],asistio=asistencia,justificacion="",idestudiante=idestudiante)
            db.session.add(nueva_asistencia)
            db.session.commit()
        session.pop('curso', None)
        session.pop('clase', None)
        session.pop('fecha', None)
        return render_template('aviso.html', mensaje="La asistencia se guardo exitosamente")
    else:
        return render_template('opciones.html')

#opcion informe detalles de cada asistencia por curso
@app.route("/informe_detalles", methods= ["POST", "GET"])
def informe_detalles():
    if request.method == 'POST':
        curso = int(request.form['curso'])

        if not curso:
            return "Por favor, complete todos los campos requeridos"
        else:
            if type(curso) == int:
                curso_est = Curso.query.filter_by(anio=curso, idpreceptor=session['id']).first()
                estudiantes = Estudiante.query.filter_by(idcurso=curso_est.id).order_by(Estudiante.apellido).all()
                listaEstudiantes=[]
                for x, estudiante in zip(range(len(estudiantes)), estudiantes):
                    asistenciass = Asistencia.query.filter_by(idestudiante=estudiante.id).all()
                    lista = [0 for x in range(7)]
                    for asistencias in asistenciass:
                        if asistencias.asistio == "n" and asistencias.codigoclase == 1 and asistencias.justificacion != "":
                            lista[2]+=1
                            lista[6]+=1
                        elif  asistencias.asistio == "n" and asistencias.codigoclase == 1 and asistencias.justificacion == "":
                            lista[3]+=1
                        if asistencias.asistio == "n" and asistencias.codigoclase == 2 and asistencias.justificacion != "":
                            lista[4]+=1
                            lista[6] += 1
                        elif asistencias.asistio == "n" and asistencias.codigoclase == 2 and asistencias.justificacion == "":
                            lista[5]+=1
                        elif asistencias.asistio == "s" and asistencias.codigoclase == 1:
                            lista[0] += 1
                        elif asistencias.asistio == "s" and asistencias.codigoclase == 2:
                            lista[1] += 1
                    listaEstudiantes.append(lista)

                #de cada estudiante:
                # cantidad de clases de aula presente,0 (clase 1)
                # cantidad de clases de educación física presente,1 (clase 2)
                # cantidad de clases de aula ausente justificadas,2
                # cantidad de clases a clases de aula ausente injustificadas,3
                # cantidad de clases de educación física ausente justificadas,4
                # cantidad de clases a clases de educación física injustificadas y5
                # cómputo de la cantidad total de inasistencias.6
                datos = zip(estudiantes,listaEstudiantes)
                return render_template("listar_estudiantes_detalles.html", datos=datos)
            else:
                return "tipo de campos erroneos, no int o  no datetime"
    else:
        return render_template('listado_asistencia.html')

#opcion Listado por curso segun clase y fecha
@app.route("/listado_asistencia", methods= ["POST", "GET"])
def listado_asist():
    if request.method == 'POST':
        curso = int(request.form['curso'])
        clase = int(request.form['clase'])

        fecha_str = request.form['fecha']
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        if not curso and not clase and not fecha:
            return "Por favor, complete todos los campos requeridos"
        else:
            if type(curso) == int and type(clase) == int and type(fecha) == datetime:
                curso_est = Curso.query.filter_by(anio=curso, idpreceptor=session['id']).first()
                estudiantes = Estudiante.query.filter_by(idcurso=curso_est.id).order_by(Estudiante.apellido).all()
                listaEstudiantes = []
                session['clase'] = clase
                for estudiante in estudiantes:
                    asistenciass = Asistencia.query.filter_by(idestudiante=estudiante.id).all()
                    lista = [0, 0]
                    for asistencias in asistenciass:
                        if asistencias.asistio == "n" and asistencias.codigoclase == clase and asistencias.fecha == fecha:
                            lista[0]+=1
                        elif asistencias.asistio == "s" and asistencias.codigoclase == clase and asistencias.fecha == fecha:
                            lista[1] += 1
                    listaEstudiantes.append(lista)
                datos = zip(estudiantes, listaEstudiantes)
                return render_template("listado_asistencia_clase.html", datos=datos)
            else:
                return "tipo de campos erroneos, no int o  no datetime"
    else:
        return render_template('listado_asistencia.html')

#Consultar inasistencias (Ingreso de padre) Consulta solo por el dni de su hijo
@app.route('/consultar_inasistencias',methods = ['GET','POST'])
def consultar_inasistencias():
    if request.method == 'POST':
        estudiante = Estudiante.query.filter_by(dni=request.form['dni']).first()
        usuariopadre = padre.query.filter_by(correo=session['name']).first()
        if estudiante is None:
            return render_template('error_dni.html')
        else:
            if estudiante.idpadre == usuariopadre.id:
                id = estudiante.id
                inasistencias = Asistencia.query.filter_by(idestudiante=id)
                total_inasis = 0
                for inasistencia in inasistencias:
                    #fechaformateada.append(inasistencia.fecha.strftime("%d-%m-%Y"))
                    if inasistencia.asistio == "n":
                        total_inasis+=1
                    elif inasistencia.codigoclase == 1:
                        inasistencia.codigoclase = "Aula"
                    else:
                        inasistencia.codigoclase = "Ed. Física"
                return render_template('listar_inasistencias.html',inasistencias = inasistencias, total = total_inasis)
            else:
                return render_template('error_estudiante.html')
    else:
        return render_template('consultar_inasistencias.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        #print("Tablas creadas correctamente")
        #cursos = Curso.query.filter_by(division=1)# trae la tabla
        #for curso in cursos:
            #print(f"ID: {curso.id}, Username: {curso.anio}, Password: {curso.division}, clave: {curso.idpreceptor}")
    app.run()
