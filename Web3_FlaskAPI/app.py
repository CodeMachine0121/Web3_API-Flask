from web3 import *
from web3.middleware import geth_poa_middleware
import json
from flask import Flask,jsonify,request,make_response
from mnemonic import Mnemonic
import pymysql
import random
import sys
from crypher import prpcrypt

w3=Web3(Web3.HTTPProvider("http://192.168.50.20:2001"))
w3.middleware_stack.inject(geth_poa_middleware, layer=0)
if w3.isConnected:
    print("Connected!")

host = "192.168.50.20"
app = Flask("Web3 Service")

cipher = prpcrypt()

name = 'james'
passwd = 'ksz54213'
sql_name = 'web3_tokens'
db_name = 'web3'


# find value in SQL
def find_priv_hash(token):
    db = pymysql.connect('localhost',name,passwd,db_name)
    cursor = db.cursor()
    mysql = 'select id from web3_tokens where token="'+token+'";'
    cursor.execute(mysql)
    data = cursor.fetchone()
    db.close()
    if data == None:
        return ""
    return data[0]


# insert value into SQL
def insert_value_sql(token,priv_hash):
    db = pymysql.connect('localhost',name,passwd,db_name)
    cursor = db.cursor()
    sql ='insert into web3_tokens(id,token) values("'+priv_hash+'","'+token +'");'
    try:
        x = cursor.execute(sql)
        db.commit()
        db.close()
        return True
    except :
        return False

def IsExit(priv_hash):
    db = pymysql.connect('localhost',name,passwd,db_name)
    cursor = db.cursor()
    mysql = 'select token from web3_tokens where  exists( select id from web3_tokens where id ="'+ priv_hash +'")'
    data = cursor.execute(mysql)
    #print('data: ',data)
    db.close()
    if data == 1:
        return True
    else :
        return False

# 驗證
def Authentication(token , priv_hash):
    
    priv_hash_sql = find_priv_hash(token)
    print('priv_hash in sql: ',priv_hash)
    ''' 
        如果 token 是錯誤的那 priv_hash_sql 會是 None
        所以要判特別斷參數 priv_hash 是否為None
    '''
    if priv_hash == "": 
        return False
    elif priv_hash == priv_hash_sql:
        print("驗證成功")
        return True
    else:
        return False

# test
@app.route('/test',methods=['POST'])
def test():
   data = request.json['test']
   return  data
# DELETE user data
@app.route('/<string:priv_hash>',methods=['DELETE'])
def RemoveData(priv_hash):
    db = pymysql.connect('localhost',name,passwd,db_name)
    cursor = db.cursor()
    sql = 'delete from '+sql_name+' where id = "'+priv_hash+'";'
    try:
        cursor.execute(sql)
        db.commit()
        db.close()
    except:
        return make_response( jsonify({'response':'Is id exist?'}),400)
    return make_response( jsonify({'response':'done'}),200)

#授權
@app.route('/get_token',methods=['POST'])
def Authorization():
    # token 用 hash 方式保存  ==  session key
    # make session key  session key=token
    print(request.json)

    token = cipher.keyMaker() #str hex
    
    print("new key: ",token)

    print("request json",request.json)
    priv_hash = request.json['id']

    priv_hash = priv_hash.replace(' ','')
    print("id: ",priv_hash)
    print("token: ",token)
    # 如果是空字串
    if priv_hash == "":
        result = 'Illegal key'
        # 422 Unprocessable Entity（
        status=422
        return make_response( jsonify({'response':result}),status )

    else:

        if IsExit(priv_hash):
            result = 'account exist'
            #    410 Gone
            status = 410
            return make_response( jsonify({'response':result}),status )
        else:
            x = insert_value_sql(token,priv_hash)

            status=200
            return make_response( jsonify({'response':token}),status )




@app.route('/transaction',methods=['POST'])
def Transaction():

    print("txn: ")
    data = request.get_json(silent =True)
    txn = data['data']#str encryption
    priv_hash = data['id']#str
    token = data['token']# str hex
    
    tokens = token.split("xx")
    key = bytes.fromhex(tokens[0])
    iv = bytes.fromhex(tokens[1])
    print(txn)
   
    if Authentication(token,priv_hash):
        
        detxn  = cipher.decrypt(txn,key,iv).split(' ')
        print("decrypt txn ", type(detxn))
        print(detxn.strip())
        if w3.isConnected():
            try:
                    # 取得交易資訊
                    rawTransaction=detxn
                  
                    #丟交易
                    tmp = w3.eth.sendRawTransaction(rawTransaction) 
                    result = "Successfully"
                    status = 200            
            except ValueError:
                    result = str(sys.exc_info()[1])
                    #result = '{' + result.split(',')[1]
                    print("error: ",result)
                    # 400 Bad request
                    status=400
                #txhasg = web3.toHex(web3.sha3(signed_txn.rawTransaction))
        else:
            result="Server not working"
            # 500 Internal Server Error
            status = 500
    else:
        result = 'Authentication failed'
        # 401 Unauthorized
        status=401
    return make_response( jsonify({'response':result}),status)

@app.route('/nonce',methods=['POST'])
def Nonce():
    
    
    token = request.json['token'] # str hex 
    address =request.json['data'] # str encrypt hex
    priv_hash = request.json['id']# str hex

    
    tokens=token.split("xx")
    key = bytes.fromhex(tokens[0])
    iv = bytes.fromhex(tokens[1])

    address = cipher.decrypt(address,key,iv).split(" ")[0]#str

    address = w3.toChecksumAddress(address)
    #convert bytes to str hex
    if Authentication(token,priv_hash):
        if w3.isConnected():
            try:
                    result = str(w3.eth.getTransactionCount(address)).encode("utf-8")
                    #encrypt result & bytes in 
                    result = cipher.encrypt(result,key,iv)
                    status = 200            
            except ValueError:
                    result = str(sys.exc_info()[1])
                    result = '{' + result.split(',')[1]
                    # 400 Bad request
                    status=400
        else:
            result="Server not working"
            # 500 Internal Server Error
            status = 500
        print("nonce:",result)
        return make_response( jsonify({'response':result}),status)
    else:
        result = 'Authentication failed'
        # 401 Unauthorized
        status=401
        return make_response( jsonify({'response':result}),status)


@app.route('/balance',methods=['POST'])
def Balance():
    try:
        address = request.json['data'] # str encrypt hex
        token = request.json['token'] # str hex
        priv_hash = request.json['id'] # str hex

        tokens = token.split("xx")
        key = bytes.fromhex(tokens[0])
        iv = bytes.fromhex(tokens[1])
        
        address = cipher.decrypt(address,key,iv).split(' ')[0] #str plaintext
        print("address: ",address)
        print("token: ",token)
        print("priv_hash: ",priv_hash)
        address = w3.toChecksumAddress(address)

    except ValueError:
        status=400  
        return make_response( jsonify({'response':'wrong fromat'}),status)
    

    if Authentication(token,priv_hash):
        if w3.isConnected():
            try:
                    #幣別: wei  = ether * 10^18
                    result = str(w3.eth.getBalance(address)/10**18).encode("utf-8")
                    result = cipher.encrypt(result,key,iv)
                    status = 200            
            except ValueError:
                    result = str(sys.exc_info()[1])
                    result = '{' + result.split(',')[1]
                    # 400 Bad request
                    status=400
        else:
            result="Server not working"
            # 500 Internal Server Error
            status = 500
        return make_response( jsonify({'response':result}),status)
    else:
        result = 'Authentication failed'
        # 401 Unauthorized
        status=401
        return make_response( jsonify({'response':result}),status)


@app.route('/forget_address',methods=['POST'] )
def Get_back_keys(): 
    # 註記碼
    mn = request.json['data'] #encrypt str
    #密碼
    passwd = request.json['passwd'] #encrypt str
    token = request.json['token'] # str
    priv_hash = request.json['id']

    print("str hex mn:",mn)

    tokens = token.split("xx")
    key = bytes.fromhex(tokens[0])
    iv = bytes.fromhex(tokens[1])

    mn = cipher.decrypt(mn,key,iv).split('\f')
    passwd = cipher.decrypt(passwd,key,iv)


    if Authentication(token,priv_hash):
        # choose the lang 
        m = Mnemonic('english')
        # get private    
        priv = w3.toHex(m.to_entropy(mn))
        # make new keyfile

        json_keyfile = str(w3.eth.account.privateKeyToAccount(priv).encrypt(passwd)).encode("utf-8")


        json_keyfile = cipher.encrypt(json_keyfile,key,iv)
        status=200
        return make_response(jsonify({'response':json_keyfile}), status)

    else:
        result = 'Authentication failed'
        # 401 Unauthorized
        status=401
        return make_response( jsonify({'response':result}),status)

    
        
    

app.run(host=host,port=5000,debug=True)





