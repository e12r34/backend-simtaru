from flask import Flask, jsonify, request, Response
from flask.views import MethodView
from flask_cors import CORS
import pymongo, json
from bson.objectid import ObjectId


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["db_simtaru"]
coll= db["cl_simtaru"]

app = Flask(__name__)

# def ubah(masukan):
#     masukan['_id']=str(masukan['_id'])
#     return masukan
def ubah(document):
    # Convert the parent ObjectId to string
    if isinstance(document.get('_id'), ObjectId):
        document['_id'] = str(document['_id'])

    # Check if 'child' field exists and is a list
    if 'child' in document and isinstance(document['child'], list):
        for child in document['child']:
            # Convert the child ObjectId to string
            if isinstance(child.get('_id'), ObjectId):
                child['_id'] = str(child['_id'])
    
    return document

class MyApiView(MethodView):
    def get(self, id=None, id_child=None):
        if id is None:
            pipeline = [
                            {
                                '$project': {
                                    '_id': 1,  # Include the _id field
                                    'nama': 1,  # Include the name field
                                    'child': {
                                        '$map': {
                                            'input': '$child',
                                            'as': 'c',
                                            'in': {
                                                '_id': '$$c._id',  # Include the child _id field
                                                'nama': '$$c.nama'  # Include the child name field
                                            }
                                        }
                                    }
                                }
                            }
                        ]
            hasil=coll.aggregate(pipeline)
            data={'data':[ubah(_data) for _data in hasil]}
            urutan=0
            output=[]
            for i in data['data']:
                suboutput={}
                suboutput['label']=i['nama']
                suboutput['data']=i['_id']
                suboutput['key']=str(urutan)
                suboutput['children']=[]
                child_urutan=0
                for j in i['child']:
                    subchild={}
                    subchild['label']=j['nama']
                    subchild['data']=j['_id']
                    subchild['parent']=i['_id']
                    subchild['key']=f"{str(urutan)}-{str(child_urutan)}"
                    child_urutan=child_urutan+1
                    suboutput['children'].append(subchild)
                urutan=urutan+1
                output.append(suboutput)
                fix_output={"root":output}
            response = Response(json.dumps(fix_output), status=200, mimetype='application/json')  
            response.headers.add('Access-Control-Allow-Origin', '*')       
            return response
        else:
            main_document_id=ObjectId(id)
            child_id=ObjectId(id_child)
            # hasil=coll.find_one({"_id":new_id}, {"geojson":1,'_id':0})
            pipeline = [
                            {
                                '$match': {
                                    '_id': main_document_id
                                }
                            },
                            {
                                '$unwind': '$child'
                            },
                            {
                                '$match': {
                                    'child._id': child_id
                                }
                            },
                            {
                                '$replaceRoot': { 'newRoot': '$child.geojson' }
                            }
                        ]
            data=coll.aggregate(pipeline)
            hasil=next(data)
            response = Response(json.dumps(hasil), status=200, mimetype='application/json')  
            response.headers.add('Access-Control-Allow-Origin', '*')       
            return response
    def post(self):
        return jsonify({'message': 'Hello, this is a POST request'})

app.add_url_rule('/api/simtaru', view_func=MyApiView.as_view('my_api_view'), methods=['GET', 'POST'])
app.add_url_rule('/api/simtaru/<id>/<id_child>', view_func=MyApiView.as_view('my_api_view_id'), methods=['GET'])

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
if __name__ == "__main__":
    app.run()