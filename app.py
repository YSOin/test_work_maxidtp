import requests
import json

from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
#import acces (token, username for DB, pass for DB)
from token_file import token, username_db, pass_db
from token_file import token
from token_file import token



#Init app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pymssql://{username_db}:{pass_db}@sql-rta.database.windows.net/maxitest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Init DB
db = SQLAlchemy(app)

#Init Marshmallow

ma = Marshmallow(app)


#Function for retriving new orders for last 7 days
def get_data_from_mysklad(token):
    time_difference = datetime.now()-timedelta(7)
    time = time_difference.strftime("%Y-%m-%d %H:%M:%S")
    url = f'https://online.moysklad.ru/api/remap/1.2/entity/customerorder?filter=moment>{time}'
    headers = {'Authorization':f'Basic {token}'}

    r = requests.get(url, headers=headers)
    data = r.json()
    data_list = []

    for item in data['rows']:
        some_data = {
                    'username':item['name'],
                    'moy_sklad_id':item['id'],
                    'moy_sklad_account_id':item['accountId'],
                    'order_date':item['created'],
                    'order_code':item['code'],
                    'order_sum':item['sum']
                    }
        data_list.append(some_data)
    return data_list

def push_data_from_mysklad():
    url = 'http://127.0.0.1:5000/order'
    headers = {'content-type': 'application/json'}
    orders = get_data_from_mysklad(token)
    for order in orders:
        r = requests.post(url,data = json.dumps(order), headers = headers)

#Order model 
class SerhiiOreders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    moy_sklad_id = db.Column(db.String(120), unique=True, nullable=False)
    moy_sklad_account_id = db.Column(db.String(120), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    order_code = db.Column(db.String(120), nullable=False) 
    order_sum = db.Column(db.Float, nullable=False)
    def __init__(self, username, moy_sklad_id, moy_sklad_account_id, order_date, order_code, order_sum):
        self.username = username
        self.moy_sklad_id = moy_sklad_id
        self.moy_sklad_account_id = moy_sklad_account_id
        self.order_date = order_date
        self.order_code = order_code
        self.order_sum = order_sum
    def __repr__(self):
        return f'<Order {self.id} {self.username}, {self.order_date}, {self.order_sum}, {self.order_code}>'


#Order Schema
class OrderSchema(ma.Schema):
    class Meta():
        fields = ('id', 'username', 'moy_sklad_id', 'moy_sklad_account_id', 'order_date', 'order_code', 'order_sum')

#init Schema
order_schema = OrderSchema()
orders_schema = OrderSchema(many = True)

#Route new orders
@app.route('/new_orders', methods=['GET'])
def get_new_orders_from_moysklad_ru():
    push_data_from_mysklad()
    return '<p>Добавлены новые заказы за последние 7 дней</p>'
@app.route('/', methods=['GET'])
def index():
    return '<h1>Тестовое задание для maxidtp</h1>'
#Add order from headers {content-type': 'application/json}
@app.route('/order', methods = ['POST'])
def add_order():
    username = request.json['username']
    moy_sklad_id = request.json['moy_sklad_id']
    moy_sklad_account_id = request.json['moy_sklad_account_id']
    order_date = request.json['order_date']
    order_code = request.json['order_code']
    order_sum = request.json['order_sum']

    new_oreder = SerhiiOreders(username, moy_sklad_id, moy_sklad_account_id, order_date, order_code, order_sum)
    
    db.session.add(new_oreder)
    db.session.commit()
    
    return order_schema.jsonify(new_oreder)

#Get all Orders
@app.route('/order', methods=['GET'])
def get_all_order():
    all_orders = SerhiiOreders.query.all()
    result = orders_schema.dump(all_orders)
    return jsonify(result)

#Get single Order
@app.route('/order/<id>', methods=['GET'])
def get_order(id):
    order = SerhiiOreders.query.get(id)
    return order_schema.jsonify(order)

#Update Order
@app.route('/order/<id>', methods = ['PUT'])
def update_order(id):
    order = SerhiiOreders.query.get(id)
    username = request.json['username']
    moy_sklad_id = request.json['moy_sklad_id']
    moy_sklad_account_id = request.json['moy_sklad_account_id']
    order_date = request.json['order_date']
    order_code = request.json['order_code']
    order_sum = request.json['order_sum']

    order.username = username
    order.moy_sklad_id = moy_sklad_id
    order.moy_sklad_account_id = moy_sklad_account_id
    order.order_date = order_date
    order.order_code = order_code
    order.order_sum = order_sum
    
    db.session.commit()
    
    return order_schema.jsonify(order)

#Run server
if __name__ == '__main__':
    app.run()
