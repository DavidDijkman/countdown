
import os
import requests
import sys

def getGoogleSeet(spreadsheet_id, outDir, outFile):
  
  url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv'
  response = requests.get(url)
  if response.status_code == 200:
    filepath = os.path.join(outDir, outFile)
    with open(filepath, 'wb') as f:
      f.write(response.content)
    #   print('CSV file saved to: {}'.format(filepath))    
  else:
    print(f'Error downloading Google Sheet: {response.status_code}')
    sys.exit(1)


##############################################

outDir = 'quotes/'

os.makedirs(outDir, exist_ok = True)
filepath = getGoogleSeet('12hadm3_zdeU7e3q-YHFfcNSDocQdzjWKnn7lzZLqhI4', outDir, "quotes.csv")

sys.exit(0); ## success
