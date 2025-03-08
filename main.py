from GPAPlannerAPP.Auth import create_app
from flask import Flask, render_template

app = create_app()




if __name__ == '__main__':
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
