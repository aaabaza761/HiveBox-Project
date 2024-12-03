from flask import Flask 
app=Flask(__name__)
@app.route('/version', methods=['GET'])
def version():
    return {"Version" : "1.0.0" }
#to eun the falsk app in any ost not 127.0.0.1 only 
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
