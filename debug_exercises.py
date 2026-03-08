from flask import Flask, jsonify
import database

app = Flask(__name__)

@app.route('/debug/exercises')
def debug_exercises():
    exercises = database.get_all_exercises()
    result = []
    for ex in exercises:
        result.append({
            'id': ex['id'],
            'name': ex['name']
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5001)