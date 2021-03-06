import sys, binascii, hashlib, time
import Crypto.PublicKey.RSA, Crypto.Random, Crypto.Cipher.AES, Crypto.Cipher.PKCS1_OAEP

# This file writes out a CSV line to store the folloing example user data,
# that may have been entered in the web form:

sample_data = {
	"barcode":  "ABCDEF",
	"name":     "Erika Musterfrau",
	"address":  "Teststr. 17, Testingen",
	"contact":  "0176-123456789",
	"password": "ErikasPW" 
}

# Read public key for encryption of contact information
with open( "public.pem", "rb" ) as f:
   public_key = Crypto.PublicKey.RSA.import_key( f.read() )
rsa_instance = Crypto.Cipher.PKCS1_OAEP.new( public_key )

# Get fingerprint of public key
md5_instance = hashlib.md5()
md5_instance.update( public_key.publickey().exportKey("DER") )
public_key_fingerprint = md5_instance.hexdigest().encode("ascii")

# Generate session key for use with AES and encrypt it with RSA
session_key = Crypto.Random.get_random_bytes( 16 ) 
encrypted_session_key = rsa_instance.encrypt( session_key )
aes_instance = Crypto.Cipher.AES.new( session_key, Crypto.Cipher.AES.MODE_CBC )  

# encode, pad, then encrypt subject data 
encrypted_subject_data = []
for s in [ sample_data["name"], sample_data["address"], sample_data["contact"] ]:
   s = s.encode( "utf-8" )
   if len(s) % 16 != 0:
      s += b'\000' * ( 16 - len(s) % 16 )
   encrypted_subject_data.append( aes_instance.encrypt( s ) )

# encode user password with SHA3
sha_instance = hashlib.sha3_384()
sha_instance.update( sample_data["password"].encode( "utf-8" ) )
password_hash = sha_instance.digest()

# Make a line for the CSV file
fields = [ 
   sample_data["barcode"].encode( "utf-8" ), 
   time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime() ).encode( "utf-8" ),
   password_hash,
   public_key_fingerprint,
   encrypted_session_key,
   aes_instance.iv ]
fields.extend( encrypted_subject_data )

# Base64-encode everything excepct for password, time stamp and public key fingerprint
for i in range( len(fields) ):
   if i not in ( 0, 1, 3 ):
      fields[i] = binascii.b2a_base64( fields[i], newline=False )

# Make line for file
line = b",".join( fields )

sys.stdout.buffer.write( line )
print()
