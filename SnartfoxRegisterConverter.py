import pandas
import json

# Read excel document
excel_data_df = pandas.read_excel('./data/Modbus-Register-SMARTFOX-Pro-SMARTFOX-Pro-2-v22e-00.01.03.10.xlsx', sheet_name='Register EM2 00.01.03.10')

# Convert excel to string
# (define orientation of document in this case from up to down)
_data = excel_data_df.to_json(orient='records')

# Print out the result
#print('Excel Sheet to JSON:\n', _data)
_data = json.loads(_data)

_store = {}
for _item in _data:
    _key = _item['Name'].replace(" ", "_")
    _store[_key] = _item
    del _item['Name']

print(json.dumps(_store))

with open('./data/SmartfoxRegister.json', 'w', encoding='utf-8') as json_file:
    json.dump(_store, json_file,ensure_ascii=False,indent=4)




