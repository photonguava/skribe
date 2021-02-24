ffrom authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'random_secret'
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="",
    client_secret="",
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

subscriptions = db.Table('subscriptions',
    db.Column('user_id',db.Integer,db.ForeignKey('user.id')),
    db.Column('page_id',db.Integer,db.ForeignKey('page.id'))
)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(128))
    name = db.Column(db.String(128))
    registered_author = db.Column(db.Boolean)
    page = db.relationship('Page',backref='user',uselist=False)
    subscribed_to = db.relationship('Page',secondary=subscriptions,backref=db.backref('subscribers'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Page(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    subdomain=db.Column(db.String(64))
    description = db.Column(db.String(360))
    banner = db.Column(db.String)
    db.pattern = db.Column(db.String)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    posts = db.relationship('Post',backref='page')


class Post(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.String)
    page_id = db.Column(db.Integer,db.ForeignKey('page.id'))

@app.route('/')
def index():
    return render_template('index.html')

auth = Blueprint('auth',__name__,url_prefix='/auth')

@auth.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('auth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()

    if user:
        login_user(user)
        return redirect(url_for('index'))
    else:
        print(user_info)
        return redirect(url_for('index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out"

profiles = Blueprint('profiles',__name__,subdomain="<subdomain>")

@profiles.route('/')
def profile(subdomain):
    page = Page.query.filter_by(subdomain=subdomain).first()
    print(page)
    return render_template('profile_base.html',posts=page.posts)


app.register_blueprint(profiles)
app.register_blueprint(auth)
if __name__ == "__main__":
    app.run(
        debug=True
    )
