# -*- coding: utf-8 -*-
"""
    :author:  update by 吴胜东 （based on Grey Li (李辉) 's  book 《flask web》）
    :license: MIT, see LICENSE for more details.
"""
import os
import uuid

from flask              import Flask, render_template, flash, redirect, url_for, request, send_from_directory, session
from flask_ckeditor     import CKEditor, upload_success, upload_fail
from flask_dropzone     import Dropzone
from flask_wtf.csrf     import validate_csrf
from wtforms            import ValidationError
from flask_sqlalchemy   import SQLAlchemy
from passlib.apps       import custom_app_context as pwd_context  #hash 单向将psw转为hash，数据库中存入hash用来比对；
from flask_httpauth     import HTTPTokenAuth,HTTPBasicAuth
from urllib.parse       import urlparse,urljoin, uses_query

from forms import LoginForm, FortyTwoForm, NewPostForm, UploadForm, MultiUploadForm, SigninForm, \
    RegisterForm, SigninForm2, RegisterForm2, RichTextForm,EquipmentRegist

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret string')

# 配置 flask.SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] =os.getenv('DATABASE_URL','sqlite:///' + os.path.join(app.root_path,'data.sqlite'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)   # create the extension
db . init_app(app)   # initialize the app with the extension
#3、在app.py中定义Role和User模型
# 使用方法： 1. 创建db
#           1.1 cd 到工作目录
#           1.2 cmd下，flask shell 输入命令from app import db,User / db.create_all() /db.drop_all()
class Role(db.Model):
    __tablename__= 'roles' 
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(64), unique=True)
    users   = db.relationship('User',backref='role')
    def _repr_(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__   = 'users' 
    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(64),db.ForeignKey('airs.owner'), unique=True, index=True)
    role_id         = db.Column(db.Integer,db.ForeignKey('roles.id'))
    password_hash   = db.Column(db.String(128))
    def _repr_(self):
        return '<User %r>' % self.username
    
    def hash_password(self, password):
        # 在cmd/flask shell/from app import db,User 下创建密码
        # qry = User.query.filter_by (username = 'wsd').first() 其中 wsd为用户名
        # qry.verify_password('123') 其中123为密码，实际需8位以上
        self.password_hash = pwd_context.encrypt(password)
        db.session.commit()

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)
    
    def create_user(self,usr_name):
        # 新建用户的页目和功能需创建（token 和 roler 认证）
        # 目前用cmd 命令实现创建 cd /工作目录/ flask shell 
        # from app import db , User
        # new_user  = User.create_user('','wsd') 创建成功则返回True，如果wsd存在，则返回False，
        usr_qry     = User.query.filter_by(username = usr_name).first()
        if usr_qry  != None:
            return  False   # 如果用户已经存在，则返回 Flase
        new_user    = User(username=usr_name)
        db.session  .add(new_user)
        db.session  .commit()
        return      True    # 返回True = 成功创建
    
    def reset_user(self,usr_name):
        # 此程序用于重置用户名的密钥清0，即用户在忘记密码时使用；
        usr_qry     = User.query.filter_by(username = usr_name).first()
        if usr_qry  == None:
            User.create_user(self,usr_name)   # 用户名不存在就创建
            return  True
        db.session  .delete(usr_qry)
        db.session  .commit()
        User.create_user(self,usr_name)
        return      True
    
class AirID(db.Model):
    # 此表为设备清单 和 user的关系表
    __tablename__   = 'airs'
    id              = db.Column(db.Integer, primary_key=True)
    airID           = db.Column(db.String(64),unique=True,index = True) #air 设备ID清单
    alias_name      = db.Column(db.String(64))
    remark          = db.Column(db.String(128))
    owner           = db.Column(db.String(64))
    
    def new_air(self,airID_arg,alias_name_arg,remark_arg,owner_arg):
        new_airline = AirID(airID=airID_arg,alias_name=alias_name_arg,remark=remark_arg,owner=owner_arg)
        db.session  .add(new_airline)
        db.session  .commit()
    
# Custom config
app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = ['png', 'jpg', 'jpeg', 'gif']

# Flask config
# set request body's max length
# app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # 3Mb

# Flask-CKEditor config
app.config['CKEDITOR_SERVE_LOCAL'] = True
app.config['CKEDITOR_FILE_UPLOADER'] = 'upload_for_ckeditor'

# Flask-Dropzone config
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'
app.config['DROPZONE_MAX_FILE_SIZE'] = 3
app.config['DROPZONE_MAX_FILES'] = 30

# 合法用户标志
app.config['USER']      = False # 合法用户标识，True = 注册用户
app.config['USERNAME']  = ""    # 用户名称全局变量

ckeditor = CKEditor(app)
dropzone = Dropzone(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/create_user',methods=['GET','POST'])
def create_user():
    User.create_user('','122')
    return render_template('index.html')

@app.route('/new_usr',methods=['Get','Post'])
def new_usr():
    form = LoginForm()
    if form.validate_on_submit():
        username    = request.form.get('username')
        psw_1       = request.form.get('password')
        psw_2       = request.form.get('re_psw')
        # 1. 核对非空 username      （在jinja中实现）
        # 2. 核对用户名是否在数据库中（在jinja中实现）
        # 3. 核对用户名 为新名称
        # 4. 核对 psw1 == psw2
        # 5. 有名
        if psw_1 != psw_2 :
            flash(f'falied, must same password !!!')
            return redirect(url_for('new_usr'))
        usr_qry = User.query.filter_by(username = username).first() 
        if usr_qry is not None:
            if usr_qry.password_hash == None:
                # 　有名无密，则创建 加密后的密码
                usr_qry.hash_password(psw_1)
                # db.session.add(usr_qry)       # 此数据在原基础上修改，非新增行；
                # db.session.commit()
                flash(f'congretulations , new user {username} activated!')
                return redirect(url_for('usr_login'))
            else:
                flash(f'系统此用户已存在,如需改密请联系我们,联系方式见 下方官网或淘宝客服 ')
                flash(f'您也可使用临时用户名:user密码:user登录')
        else:
            flash(f'请与我们联系创建 新用户名, 联系方式见下方官网或淘宝客服')
    return  render_template('new_usr.html', form=form)

@app.route('/usr_login',methods=['Get','Post'])
def usr_login():
    form = LoginForm()
    if request.method == 'POST':
        username    = request.form.get('username')
        password    = request.form.get('password')
        if username =='user':
            flash   (f'欢迎临时用户{username} , 或联系我们注册新账号')
            return redirect(url_for('index'))   # 跳转到正确的页目
        usr_qry     = User.query.filter_by(username = username).first() 
        if usr_qry  == None:
            flash(f'user: {username} not register ,pls fill right name or contact us!')
            return redirect(url_for('usr_login'))
        if usr_qry.verify_password(password):
            # 系统中存的密码 和算出来的密码一致
            app.config['USERNAME'] = username
            app.config['USER']     = True
            flash(f'welcome {username}!')
            return redirect(url_for('index'))   # 跳转到正确的页目
        else:
            flash(f'Password Wrong,pls check !')
            flash(f'密码错误,请核对是否注册激活')
    return  render_template('usr_login.html', form=form)

@app.route('/equipment_regist',methods=['GET','POST'])
def equipment_regist():
    form = EquipmentRegist()
    if app.config['USER']   != True:
        form.alert_msg.val  = ('请先登记')
        form.alert_msg.type = 'alert-warning'
        form.alert_msg.bool = True
        return redirect(url_for('usr_login'))
    form.username.data = app.config['USERNAME']
    if request.method == 'POST':
        #开始登记入 db
        rslt = form.validate_on_submit()
        air_id  = form.equipmentID.data
        air_lbl = form.equipmentID.label.text
        alias_n = form.alias_name.data
        remark  = form.eqp_remark.data
        usr_n   = form.username.data
        if rslt == True:
            air_qry = AirID.query.filter_by(airID = air_id).first()
            if air_qry == None:
                AirID.new_air('',air_id,alias_n,remark,usr_n)
                form.alert_msg.bool = True
                form.alert_msg.type = 'alert-info'
                form.alert_msg.val  = f'{air_id} 录入成功!'
            else:
                form.alert_msg.val  = (f'pls ck,{air_lbl}={air_id} already exits')
                form.alert_msg.type = 'alert-warning'
                form.alert_msg.bool = True                
                # form.alert_msg = (f'pls ck,{air_lbl}={air_id} already exits')
        else:
            form.alert_msg.val  = f'pls ck, {air_lbl}={air_id},必须15位数字 以86格式开头'
            form.alert_msg.type = 'alert-warning'
            form.alert_msg.bool = True    
            # form.alert_msg = f'pls ck, {air_lbl}={air_id},15位数字 exp:86...'
    return render_template('equipment_regist.html', form=form)

@app.route('/html', methods=['GET', 'POST'])
def html():
    form = LoginForm()
    if request.method == 'POST':
        username = request.form.get('username')
        flash('Welcome home, %s!' % username)
        return redirect(url_for('index'))
    return render_template('pure_html.html')


@app.route('/basic', methods=['GET', 'POST'])
def basic():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        flash('Welcome home, %s!' % username)
        return redirect(url_for('index'))
    return render_template('basic.html', form=form)

@app.route('/bootstrap', methods=['GET', 'POST'])
def bootstrap():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        flash('Welcome home, %s!' % username)
        return redirect(url_for('index'))
    return render_template('bootstrap.html', form=form)


@app.route('/custom-validator', methods=['GET', 'POST'])
def custom_validator():
    form = FortyTwoForm()
    if form.validate_on_submit():
        flash('Bingo!')
        return redirect(url_for('index'))
    return render_template('custom_validator.html', form=form)


@app.route('/uploads/<path:filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)


@app.route('/uploaded-images')
def show_images():
    return render_template('uploaded.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def random_filename(filename):
    ext = os.path.splitext(filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.photo.data
        filename = random_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        flash('Upload success.')
        session['filenames'] = [filename]
        return redirect(url_for('show_images'))
    return render_template('upload.html', form=form)


@app.route('/multi-upload', methods=['GET', 'POST'])
def multi_upload():
    form = MultiUploadForm()

    if request.method == 'POST':
        filenames = []

        # check csrf token
        try:
            validate_csrf(form.csrf_token.data)
        except ValidationError:
            flash('CSRF token error.')
            return redirect(url_for('multi_upload'))

        # check if the post request has the file part
        if 'photo' not in request.files:
            flash('This field is required.')
            return redirect(url_for('multi_upload'))

        for f in request.files.getlist('photo'):
            # if user does not select file, browser also
            # submit a empty part without filename
            # if f.filename == '':
            #     flash('No selected file.')
            #    return redirect(url_for('multi_upload'))
            # check the file extension
            if f and allowed_file(f.filename):
                filename = random_filename(f.filename)
                f.save(os.path.join(
                    app.config['UPLOAD_PATH'], filename
                ))
                filenames.append(filename)
            else:
                flash('Invalid file type.')
                return redirect(url_for('multi_upload'))
        flash('Upload success.')
        session['filenames'] = filenames
        return redirect(url_for('show_images'))
    return render_template('upload.html', form=form)


@app.route('/dropzone-upload', methods=['GET', 'POST'])
def dropzone_upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'This field is required.', 400
        f = request.files.get('file')

        if f and allowed_file(f.filename):
            filename = random_filename(f.filename)
            f.save(os.path.join(
                app.config['UPLOAD_PATH'], filename
            ))
        else:
            return 'Invalid file type.', 400
    return render_template('dropzone.html')


@app.route('/two-submits', methods=['GET', 'POST'])
def two_submits():
    form = NewPostForm()
    if form.validate_on_submit():
        if form.save.data:
            # save it...
            flash('You click the "Save" button.')
        elif form.publish.data:
            # publish it...
            flash('You click the "Publish" button.')
        return redirect(url_for('index'))
    return render_template('2submit.html', form=form)


@app.route('/multi-form', methods=['GET', 'POST'])
def multi_form():
    signin_form = SigninForm()
    register_form = RegisterForm()

    if signin_form.submit1.data and signin_form.validate():
        username = signin_form.username.data
        flash('%s, you just submit the Signin Form.' % username)
        return redirect(url_for('index'))

    if register_form.submit2.data and register_form.validate():
        username = register_form.username.data
        flash('%s, you just submit the Register Form.' % username)
        return redirect(url_for('index'))

    return render_template('2form.html', signin_form=signin_form, register_form=register_form)


@app.route('/multi-form-multi-view')
def multi_form_multi_view():
    signin_form = SigninForm2()
    register_form = RegisterForm2()
    return render_template('2form2view.html', signin_form=signin_form, register_form=register_form)


@app.route('/handle-signin', methods=['POST'])
def handle_signin():
    signin_form = SigninForm2()
    register_form = RegisterForm2()

    if signin_form.validate_on_submit():
        username = signin_form.username.data
        flash('%s, you just submit the Signin Form.' % username)
        return redirect(url_for('index'))

    return render_template('2form2view.html', signin_form=signin_form, register_form=register_form)


@app.route('/handle-register', methods=['POST'])
def handle_register():
    signin_form = SigninForm2()
    register_form = RegisterForm2()

    if register_form.validate_on_submit():
        username = register_form.username.data
        flash('%s, you just submit the Register Form.' % username)
        return redirect(url_for('index'))
    return render_template('2form2view.html', signin_form=signin_form, register_form=register_form)


@app.route('/ckeditor', methods=['GET', 'POST'])
def integrate_ckeditor():
    form = RichTextForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        flash('Your post is published!')
        return render_template('post.html', title=title, body=body)
    return render_template('ckeditor.html', form=form)


# handle image upload for ckeditor
@app.route('/upload-ck', methods=['POST'])
def upload_for_ckeditor():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
    url = url_for('get_file', filename=f.filename)
    return upload_success(url, f.filename)
