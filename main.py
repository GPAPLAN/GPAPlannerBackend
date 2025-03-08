from GPAPlannerAPP.auth import create_app
from flask import Flask, render_template

app = create_app()




if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
