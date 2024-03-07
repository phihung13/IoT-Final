from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import pymongo, os, logging
from datetime import datetime
from fastapi.responses import JSONResponse
################################################################################
logging.basicConfig(level=logging.DEBUG)
app = FastAPI()
################################################################################
field_ids = {
    "field1": 0,  #led 1 
    "field2": 0,  #led 2
    "field3": 0,  #servo
    "field4": 0,  #temp
    "field5": 0,  #humi
    "field6": 0,  #rotary
    "field7": 0,  #moisture
    "field8": 0,  #sonic
    "field9": 0,  #lcd
    "field10": 0,  #4digit display
    "field11": 0,  #sw1
    "field12": 0,  #sw2
    "field13": 0,  #lamp
    "field14": 0,  #siren   
}
# Đọc giá trị ID từ tệp trạng thái (nếu tồn tại)
def load_last_ids():
    if os.path.exists("last_ids.txt"):
        with open("last_ids.txt", "r") as file:
            for line in file:
                field, value = line.strip().split(":")
                field_ids[field] = int(value)
# Lưu giá trị ID vào tệp trạng thái
def save_last_ids():
    with open("last_ids.txt", "w") as file:
        for field, value in field_ids.items():
            file.write(f"{field}:{value}\n")
#####################################################################################################  
myclient = pymongo.MongoClient('mongodb+srv://hung:hung@hung.jnqwxl7.mongodb.net/?retryWrites=true&w=majority')
mydb = myclient["mydatabase"]
mycol1 = mydb["Field 1"]
mycol2 = mydb["Field 2"]
mycol3 = mydb["Field 3"]
mycol4 = mydb["Field 4"]
mycol5 = mydb["Field 5"]
mycol6 = mydb["Field 6"]
mycol7 = mydb["Field 7"]
mycol8 = mydb["Field 8"]
mycol9 = mydb["Field 9"]
mycol10 = mydb["Field 10"]
mycol11 = mydb["Field 11"]
mycol12 = mydb["Field 12"]
mycol13 = mydb["Field 13"]
mycol14 = mydb["Field 14"]

class Item(BaseModel):
    field1: int = None
    field2: int = None
    field3: int = None
    field4: int = None
    field5: int = None
    field6: int = None
    field7: int = None
    field8: int = None
    field9: str = None  #LCD kiểu string
    field10: str = None #4digit kiểu string
    field11: int = None
    field12: int = None
    field13: int = None
    field14: int = None
##########################################################################################
def verify_api_key(api_key: str = Query(...)):
    if api_key != "ABC":
        raise HTTPException(status_code=401, detail="Unauthorized")
##########################################################################################
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    logging.error(f"An error occurred: {exc}")
    return {"error": "An error occurred"}, 500
##########################################################################################
@app.get("/latest_data")
async def get_latest_data():
    try:
        latest_data = {}
        collections = [mycol1, mycol2, mycol3, mycol4, mycol5, mycol6, mycol7, mycol8, mycol9, mycol10, mycol11, mycol12, mycol13, mycol14]
        
        for collection in collections:
            data = collection.find_one(sort=[('time', pymongo.DESCENDING)])
            if data is not None:
                data.pop('_id')
                latest_data[collection.name] = data
                
        return latest_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Máy chủ {str(e)}")
##############################################################################################
@app.get("/data/{field_name}")
async def get_data(field_name: str):
    collections = {
    "field1": mydb["Field 1"],
    "field2": mydb["Field 2"],
    "field3": mydb["Field 3"],
    "field4": mydb["Field 4"],
    "field5": mydb["Field 5"],
    "field6": mydb["Field 6"],
    "field7": mydb["Field 7"],
    "field8": mydb["Field 8"],
    "field9": mydb["Field 9"],
    "field10": mydb["Field 10"],
    "field11": mydb["Field 11"],
    "field12": mydb["Field 12"],
    "field13": mydb["Field 13"],
    "field14": mydb["Field 14"],
    }
    if field_name in collections:
        collection = collections[field_name]
        data = collection.find_one(sort=[('time', pymongo.DESCENDING)])
        if data:
            data.pop('_id')
            # Lấy giá trị của tất cả các trường trừ '_id', 'time', và 'device'
            field_values = {key: value for key, value in data.items() if key not in ['_id', 'time', 'device']}
            return JSONResponse(content=field_values)
        else:
            return JSONResponse(content={"message": "No data available for this field."}, status_code=404)
    else:
        return JSONResponse(content={"message": "Invalid field name."}, status_code=400)
##################################################################################################
@app.get("/data_value/{field_name}")
async def get_data_value(field_name: str):
    collections = {
        "field1": mydb["Field 1"],
        "field2": mydb["Field 2"],
        "field3": mydb["Field 3"],
        "field4": mydb["Field 4"],
        "field5": mydb["Field 5"],
        "field6": mydb["Field 6"],
        "field7": mydb["Field 7"],
        "field8": mydb["Field 8"],
        "field9": mydb["Field 9"],
        "field10": mydb["Field 10"],
        "field11": mydb["Field 11"],
        "field12": mydb["Field 12"],
        "field13": mydb["Field 13"],
        "field14": mydb["Field 14"]
    }
    if field_name in collections:
        collection = collections[field_name]
        data = collection.find_one(sort=[('time', pymongo.DESCENDING)])
        if data:
            return JSONResponse(content=data[field_name])
        else:
            return JSONResponse(content={"message": "No data available for this field."}, status_code=404)
    else:
        return JSONResponse(content={"message": "Invalid field name."}, status_code=400)
##########################################################################################
@app.post("/update_post")
async def update_data_post(item: Item, api_key: str = Depends(verify_api_key)):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = "pi_nhom1"

    fields = {k: v for k, v in item.model_dump().items() if v is not None}

    try:
        field_name = None
        for key in fields:
            if key in field_ids:
                field_name = key
                break

        if field_name:
            # Sử dụng trạng thái ID của từng trường
            data = {
                "_id": field_ids[field_name] + 1,
                "time": time,
                "device": device,
                **fields,
            }

            collection = None
            if field_name == "field1":
                collection = mycol1
            elif field_name == "field2":
                collection = mycol2
            elif field_name == "field3":
                collection = mycol3
            elif field_name == "field4":
                collection = mycol4
            elif field_name == "field5":
                collection = mycol5
            elif field_name == "field6":
                collection = mycol6
            elif field_name == "field7":
                collection = mycol7
            elif field_name == "field8":
                collection = mycol8
            elif field_name == "field9":
                collection = mycol9
            elif field_name == "field10":
                collection = mycol10
            elif field_name == "field11":
                collection = mycol11
            elif field_name == "field12":
                collection = mycol12
            elif field_name == "field13":
                collection = mycol13
            elif field_name == "field14":
                collection = mycol14
            if collection is not None:
                collection.insert_one(data)
                # Cập nhật trạng thái ID của trường
                field_ids[field_name] = data["_id"]
            save_last_ids()

            return {"message": "Data inserted successfully", "_id": data["_id"], "time": time, "device": device, **fields}
        else:
            return {"message": "No valid field name in the data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
###########################################################################################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
