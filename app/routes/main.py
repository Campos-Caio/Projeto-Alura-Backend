from flask import Blueprint, jsonify, request, current_app
from app.models.products import *
from app.models.sale import *
from app.models.user import LoginPayLoad
from app.decorators import token_required
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
from bson import ObjectId
import jwt 
import csv 
import os 
import io 

main_bp = Blueprint('main_bp', __name__)


@main_bp.route('/')
def index(): 
    return jsonify({'message': 'Bem vindo ao StyleSync!'})

# O sistema deve permitir que o usuario faça o login com username e password
@main_bp.route('/login', methods=['POST'])
def login():
    try: 
        raw_data = request.get_json()
        user_data = LoginPayLoad(**raw_data)
    except ValidationError as error:
        return jsonify({'error': error.errors()}), 400
    except Exception as error:
        return jsonify({'error': f"Erro ao realizar o login! {str(error)}"}), 500 

    if user_data.username == 'admin' and user_data.password == 'supersecret': 
        token = jwt.encode(
            {
                'user_id' : user_data.username, 
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30), 
            }, 
            current_app.config["SECRET_KEY"], 
            algorithm='HS256'
        )

        return jsonify({'acess_token' : token}, 200)
    return jsonify({'error' : 'Credenciais Invalidas!'}), 401


# O sistema deve permitir listar os produtos
@main_bp.route('/products', methods=['GET'])
def get_products():
    db = current_app.db
    products_cursor = db.products.find({}) # Busca todos os documentos dentro da collection products 
    products_list = [ProductDBModel(**product).model_dump(by_alias=True, exclude_none=True) for product in products_cursor] 
    return jsonify(products_list)

# O sistema deve permitir a criacao de produtos 
@token_required
@main_bp.route('/product', methods=['POST'] )
def create_product(token):
    db = current_app.db
    try: 
        product = Product(**request.get_json())
    except ValidationError as error: 
        return jsonify({'error': error.errors()})
    
    result = db.products.insert_one(product.model_dump())
    return jsonify({'message': 'O produto foi criado corretamente!', 
                    'id' : str(result.inserted_id)}), 201  

# O sistema deve permitir visualizar um produto especifico
@main_bp.route('/product/<string:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    db = current_app.db
    try: 
        oid = ObjectId(product_id)
    except Exception as error: 
        return jsonify({"error:" :f"Erro ao transformar o {product_id} em ObjectID: {error}"})
    
    product = db.products.find_one({'_id':oid})
    
    if product: 
        product_model = ProductDBModel(**product).model_dump(by_alias=True, exclude_none=True)
        return jsonify(product_model)
    else:
        return jsonify({'error': f'Erro ao buscar produto de ID {product_id} : {error}!'})

# O sistema deve permitir atualizar um produto especifico
@main_bp.route('/product/<string:product_id>', methods=['PUT'])
@token_required
def update_product(token, product_id):
    db = current_app.db 
    try: 
        oid = ObjectId(product_id)
        updated_data = UpdateProduct(**request.get_json())
    except ValidationError as error: 
        return jsonify({"error": error.errors()})
    
    updated_result = db.products.update_one(
        {'_id':oid}, 
        {"$set": updated_data.model_dump(exclude_unset=True)}
    )

    if updated_result.matched_count == 0: 
        return jsonify({"error": "Produto nao encontrado!"}), 404
    
    updated_product = db.products.find_one({"_id":oid})
    return jsonify(ProductDBModel(**updated_product).model_dump(by_alias=True, exclude_none=True))

# O sistema deve permitir deletar um produto especifico
@main_bp.route('/product/<string:product_id>', methods=['DELETE'])
@token_required
def delete_product(token, product_id):
    db = current_app.db
    try: 
        oid = ObjectId(product_id)
    except ValidationError as error: 
        return jsonify({"error": "ID do produto invalido!"}), 400
    
    deleted_product = db.products.delete_one({"_id" : oid})

    if deleted_product.deleted_count == 0: 
        return jsonify({"error": "O produto nao foi encontrado"}), 404
    
    return "", 204

# O sistema deve permitir dar uploado em produtos
@main_bp.route('/sales/upload', methods=['POST'])
@token_required 
def upload_sales(token):

    db = current_app.db
    if 'file' not in request.files: 
        return jsonify({"error": "Nenhum arquivo foi enviado"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo foi selecionado"}), 400

    if file and file.filename.endswith('.csv'): 
        csv_stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
        csv_reader = csv.DictReader(csv_stream)

        sales_to_insert = []
        error = []

        for row_num, row in enumerate(csv_reader, 1): 
            try: 
               sale_data =  Sale(**row)

               sales_to_insert.append(sale_data.model_dump())

            except ValidationError as error: 
                error.append(f"Linha {row_num} com dados invalidos!")
            except Exception as error: 
                error.append(f"Linha {row_num} com error inesperados!")
                
        if sales_to_insert: 
            try: 
                db.sale.insert_many(sales_to_insert)
            except Exception as error:
                return jsonify({"error": f'{error}'})
        
        return jsonify({'message' : "Leitura do arquivo CSV completa!", 
                        'vendas_passadas':len(sales_to_insert), 
                        'erros_encontrados':error}), 200




    return jsonify({'message': f'Essa eh a rota de upload de vendas!'})
 
