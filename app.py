from flask import Flask, render_template

# Inicializar a aplicação
app = Flask(__name__,template_folder="frontend/templates")

# ============= ROUTES =============
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')
@app.route('/artigos', methods=['GET'])
def article():
        return render_template('article.html')

@app.route('/favoritos', methods=['GET'])
def favourites():
        return render_template('favourites.html')
@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('login.html')

@app.route('/preferencias', methods=['GET'])
def preferences():
        return render_template('preferences.html')

@app.route('/register', methods=['GET','POST'])
def register():
        return render_template('register.html')


# ============= MAIN =============
if __name__ == '__main__':
    app.run(debug=True, port=5000)