from flask import Flask 
app=Flask(__name__)
@app.route('/version', methods=['GET'])
def version():
    return {"Version" : "1.0.0" }
if __name__ == "__main__":
    app.run(debug=True)