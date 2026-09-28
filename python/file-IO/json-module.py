import json

py_obj = {
        "id": "item_001",
        "name": "Wireless Headphones",
        "category": "Electronics",
        "price": 149.99,
        "in_stock": True,
        "tags": ["audio", "bluetooth", "gadget"]
      }
json_str = json.dumps(py_obj)
print(type(json_str),json_str)

with open("data.json","r") as f:
    data = json.load(f)
    # data = json.dump(py_obj,f,indent=4,sort_keys=True)
    print(data)