import sys  
from Crypto.Cipher import AES  
from Crypto import Random
from binascii import b2a_hex, a2b_hex  
   
class prpcrypt():  
    def __init__(self):  
        self.mode = AES.MODE_CBC  
    def keyMaker(self): # key & iv
        return Random.new().read(AES.block_size).hex()+"xx"+Random.new().read(16).hex()
    #加密函數，如果text不是16的倍數【加密文本text必須為16的倍數！】，那就補足為16的倍數  
    def encrypt(self, text,key,iv):  
        cryptor = AES.new(key, self.mode, iv)  
        #這裏密鑰key 長度必須為16（AES-128）、24（AES-192）、或32（AES-256）Bytes 長度.目前AES-128足夠用  
        length = 16  
        count = len(text)  
        if(count % length != 0) :  
            add = length - (count % length)  
        else:  
            add = 0  
        text = text + (b"\b" * add)  
        ciphertext = cryptor.encrypt(text)  
        #因為AES加密時候得到的字符串不一定是ascii字符集的，輸出到終端或者保存時候可能存在問題  
        #所以這裏統一把加密後的字符串轉化為16進制字符串  
        return ciphertext.hex()  
    
    #解密後，去掉補足的空格用strip() 去掉  
    def decrypt(self,text,key,iv):  
        cryptor = AES.new(key, self.mode, iv)  
        plain_text = cryptor.decrypt(bytes.fromhex(text)).decode()
        print("decrypt: ",plain_text.strip('\b').strip(" "))

        return plain_text.strip('\b').strip(" ")

    

