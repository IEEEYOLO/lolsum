import firebase_admin
from firebase_admin import credentials, firestore, storage

# Use the application default credentials
cred = credentials.Certificate("./lolsum-b9440-firebase-adminsdk-thwlv-7cda72cce9.json")
firebase_admin.initialize_app(cred, {
  'storageBucket': 'lolsum-b9440.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()


blob = bucket.blob('hi.txt')
blob.upload_from_filename('hi.txt')
# doc_ref = db.collection(u'collection').document(u'1')
# doc_ref.set({
#     u'first': u'Ada',
#     u'last': u'Lovelace',
#     u'born': 1815
# })