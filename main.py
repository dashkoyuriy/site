from flask import Flask, redirect, request, abort
from data import db_session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask import render_template
from data.table import User
from data.table import Jobs
from data.table import Departaments
from data.table import Categories
from flask_login import LoginManager, login_user, login_required, logout_user, current_user


db_session.global_init('db\site.sqlite')
session = db_session.create_session()
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


class RegisterForm(FlaskForm):
    email = EmailField('Login / email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat password', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    age = StringField('Age', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    speciallity = StringField('Speciallity', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddJobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    team_leader = StringField('Team leader id', validators=[DataRequired()])
    work_size = StringField('Work Size', validators=[DataRequired()])
    collaborators = StringField('Collaborators', validators=[DataRequired()])
    category = StringField('Hazard Category', validators=[DataRequired()])
    is_finished = BooleanField('Is job finished?')
    submit = SubmitField('Submit')


class AddDepForm(FlaskForm):
    title = StringField('Departament Title', validators=[DataRequired()])
    chief = StringField('Chief id', validators=[DataRequired()])
    members = StringField('Members', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


def bool_to_name(s):
    if s:
        return 'Is finished'
    else:
        return 'Is not Finished'


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    params = {}
    params['head1'] = "Учебный сайт с базой данных"
    params['head4'] = "Яндекс Лицей"
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            address=form.address.data,
            position=form.position.data,
            speciality=form.speciallity.data,
            age=form.age.data,
            surname=form.surname.data
            
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', form=form, title='Регистрация', **params)


@app.route('/login', methods=['GET', 'POST'])
def login():
    params = {}
    params['head1'] = "Учебный сайт с базой данных"
    params['head4'] = "Яндекс Лицей"
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form, **params)


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        params = {}
        params['title'] = "Журнал работ"
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        jobs_out = []
        for job_p in session.query(Jobs).all():
            jobs_out.append([job_p.job,
                             str(session.query(User).filter(User.id == job_p.team_leader).first().surname) + ' ' + str(session.query(User).filter(User.id == job_p.team_leader).first().name),
                             job_p.work_size,
                             job_p.collaborators,
                             bool_to_name(job_p.is_finished),
                             job_p.id,
                             job_p.user,
                             session.query(Categories).filter(Categories.job_id == job_p.id).first().category
                             ])
        params['jobs'] = jobs_out
        return render_template('index.html', **params)
    return redirect('/login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    if current_user.is_authenticated:
        params = {}
        params['type_act'] = 'Adding a Job'
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        form = AddJobForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            job_p = Jobs()
            job_p.team_leader=form.team_leader.data
            job_p.job=form.title.data
            job_p.work_size=form.work_size.data
            job_p.collaborators=form.collaborators.data
            job_p.is_finished=form.is_finished.data
            job_p.user_id=current_user.id
            current_user.jobs.append(job_p)
            session.merge(current_user)
            session.commit()
            id = session.query(Jobs).filter(Jobs.job == job_p.job,
                                            Jobs.team_leader == job_p.team_leader,
                                            Jobs.user_id == job_p.user_id).first().id
            session = db_session.create_session()
            cat = Categories()
            cat.job_id = id
            cat.category = form.category.data
            session.add(cat)
            session.commit()
            return redirect('/')
        return render_template('addJob.html', form=form, title='Adding a job', **params)
    return redirect('/login')


@app.route('/edit_job/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    if current_user.is_authenticated:
        params = {}
        params['type_act'] = 'Adding a Job'
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        form = AddJobForm()
        if request.method == "GET":
            session = db_session.create_session()
            job_p = session.query(Jobs).filter(Jobs.id == id, 
                                              (Jobs.user == current_user) | (current_user.id == 1)).first()
            if job_p:
                form.team_leader.data=job_p.team_leader
                form.title.data=job_p.job
                form.work_size.data=job_p.work_size
                form.collaborators.data=job_p.collaborators
                form.is_finished.data=job_p.is_finished
                category = session.query(Categories).filter(Categories.job_id == id).first().category
                form.category.data=category
            else:
                abort(404)
        if form.validate_on_submit():
            session = db_session.create_session()
            job_p = session.query(Jobs).filter(Jobs.id == id, 
                                              (Jobs.user == current_user) | (current_user.id == 1)).first()
            if job_p:
                job_p.team_leader=form.team_leader.data
                job_p.job=form.title.data
                job_p.work_size=form.work_size.data
                job_p.collaborators=form.collaborators.data
                job_p.is_finished=form.is_finished.data
                session.commit()
                session = db_session.create_session()
                category=form.category.data
                hazard = session.query(Categories).filter(Categories.job_id == id).first()
                print(hazard.job_id)
                hazard.category=category
                session.commit()
                return redirect('/')
            else:
                abort(404)
        return render_template('addJob.html', form=form, title='Editing a job', **params)
    return redirect('/login')


@app.route('/job_delete/<int:id>', methods=['GET', 'POST'])
def del_job(id):
    if current_user.is_authenticated:
        session = db_session.create_session()
        job_p = session.query(Jobs).filter(Jobs.id == id, 
                                            (Jobs.user == current_user) | (current_user.id == 1)).first()
        if job_p:
            session.delete(job_p)
            session.commit()
            session = db_session.create_session()
            hazard = session.query(Categories).filter(Categories.job_id == id).first()
            session.delete(hazard)
            session.commit()
        else:
            abort(404)
        return redirect('/')
    return redirect('/login')


@app.route('/adddep', methods=['GET', 'POST'])
def adddep():
    if current_user.is_authenticated:
        params = {}
        params['type_act'] = 'Adding a Departament'
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        form = AddDepForm()
        if form.validate_on_submit():
            session = db_session.create_session()
            dep_p = Departaments()
            dep_p.title=form.title.data
            dep_p.chief=form.chief.data
            dep_p.members=form.members.data
            dep_p.email=form.email.data
            dep_p.user_id=current_user.id
            current_user.deps.append(dep_p)
            session.merge(current_user)
            session.commit()
            return redirect('/departaments')
        return render_template('addDep.html', form=form, title='Adding a Departamen', **params)
    return redirect('/login')


@app.route('/edit_dep/<int:id>', methods=['GET', 'POST'])
def edit_dep(id):
    if current_user.is_authenticated:
        params = {}
        params['type_act'] = 'Editing a Departament'
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        form = AddDepForm()
        if request.method == "GET":
            session = db_session.create_session()
            dep_p = session.query(Departaments).filter(Departaments.id == id, 
                                              (Departaments.user == current_user) | (current_user.id == 1)).first()
            if dep_p:
                form.title.data=dep_p.title
                form.chief.data=dep_p.chief
                form.members.data=dep_p.members
                form.email.data=dep_p.email
            else:
                abort(404)
        if form.validate_on_submit():
            session = db_session.create_session()
            dep_p = session.query(Departaments).filter(Departaments.id == id, 
                                              (Departaments.user == current_user) | (current_user.id == 1)).first()
            if dep_p:
                dep_p.title=form.title.data
                dep_p.chief=form.chief.data
                dep_p.members=form.members.data
                dep_p.email=form.email.data
                session.commit()
                return redirect('/departaments')
            else:
                abort(404)
        return render_template('addDep.html', form=form, title='Editing a Departament', **params)
    return redirect('/login')


@app.route('/dep_delete/<int:id>', methods=['GET', 'POST'])
def del_dep(id):
    if current_user.is_authenticated:
        session = db_session.create_session()
        dep_p = session.query(Departaments).filter(Departaments.id == id, 
                                            (Departaments.user == current_user) | (current_user.id == 1)).first()
        if dep_p:
            session.delete(dep_p)
            session.commit()
        else:
            abort(404)
        return redirect('/departaments')
    return redirect('/login')


@app.route('/departaments')
def dep_list_str():
    if current_user.is_authenticated:
        params = {}
        params['title'] = "List of Departaments"
        params['head1'] = "Учебный сайт с базой данных"
        params['head4'] = "Яндекс Лицей"
        deps_out = []
        for dep_p in session.query(Departaments).all():
            deps_out.append([dep_p.title,
                             str(session.query(User).filter(User.id == dep_p.chief).first().surname) + ' ' + str(session.query(User).filter(User.id == dep_p.chief).first().name),
                             dep_p.members,
                             dep_p.email,
                             dep_p.id,
                             dep_p.user])
        params['deps'] = deps_out
        return render_template('departaments.html', **params)
    return redirect('/login')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
