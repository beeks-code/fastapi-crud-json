from fastapi import FastAPI,Path,Query,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field,computed_field
from typing import Annotated,Literal,Optional
import json 


class Patient(BaseModel):
    id: Annotated[str, Field(..., description='ID of the patient', examples=['P001'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Literal['male', 'female']
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in kgs')]
    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Normal'
        else:
            return 'Obese'
        

## Update pydantic model to Update the patient by data
class UpdatePatient(BaseModel):
    name:Annotated[Optional[str],Field(default=None)]
    city:Annotated[Optional[str],Field(default=None)]
    age:Annotated[Optional[int],Field(default=None,gt=0,lt=120)]
    gender:Annotated[Optional[Literal["male","female"]],Field(default=None)]
    height:Annotated[Optional[float],Field(default=None,gt=0)]
    weight:Annotated[Optional[float],Field(default=None,gt=0)]



    ### to load json file
def load_data():
    with open("patient.json","r") as file:
        data=json.load(file)
    return data    
## to save json file
def save_data(data):
    with open("patient.json","w") as file:
        json.dump(data,file)    

app=FastAPI()

@app.get("/")
def welcome():
    return "Welcome to our website"

@app.post('/create')
def get_data(patient:Patient):
    ## loading data
    data=load_data()
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient already exists")
    data[patient.id] = patient.model_dump(exclude=['id']) ## now new patient added to data dictionary
    save_data(data)  ## each time this function is called we rewrite the jason file

    return JSONResponse(status_code=201, content={"message":"Patient added sucessfully"})


## we will use path function to document path function
@app.get('/patient/{p_id}')
def view_patient(p_id:str = Path(...,description="Id of patient ",example="P001")):  ## 3 dots means parameter is needed
    jsndata=load_data()  #
    p_id=p_id.capitalize()
    if p_id in jsndata:
        return f"{jsndata[p_id]} is the result found"
    
    raise HTTPException(status_code=404,detail='Patient not found')  ## raising http error


@app.get("/sort/{sort_by}/{order}")
def sort_using_path_parameter(sort_by:str=Path(...,description="Sort on the basis of height, weight, or BMI",example="height"),
                          order:str=Path(...,description="Order of sorting asc or desc")):
    valid_field=["height","weight","bmi"]
    valid_order=["asc","desc"]
    if sort_by not in valid_field:
        raise HTTPException(status_code=400,detail="Invalid field")
    if order not in valid_order:
        raise HTTPException(status_code=400,detail="Invalid order")
    order_tf=True if order=="desc" else False
    data=load_data()
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=order_tf)
    return sorted_data

###   localhost/sort?sort_by=height&order=desc

@app.get("/sort")
def sort_patient(sort_by:str=Query(...,description="Sort on the basis of height, weight, or BMI"), 
                 order:str=Query("asc",description="Model of sorting")): ## asc is defalut 
    
    ## due to 3 dot sort_by is mandatory but order is optional and default value is asc
    
    valid_field=["height","weight","bmi"]
    valid_order=["asc","desc"]
    sort_by=sort_by.lower()
    order=order.lower()
    if sort_by not in valid_field:
        raise HTTPException(status_code=400,detail=f"Invalide Field only {valid_field} accepted")
    if order not in valid_order:
        raise HTTPException(status_code=400,detail=f"Invalid order, only {valid_order} are the options")    
    order_tf=True if order=="desc" else False
    data=load_data()
    ## sorting logic
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=order_tf)
    return sorted_data


@app.put("/update/{p_id}")
def update(patient:UpdatePatient,p_id:str):
    data=load_data()
    p_id=p_id.capitalize()
    if p_id not in data:
        raise HTTPException(status_code=400,detail="Patient not found")
    
    old_data=data[p_id]
    new_data=patient.model_dump(exclude_unset=True) ## only updated fields are selected

    for key,value in new_data.items():
        new_data[key]=value

    new_data["id"]=p_id
    new_data=Patient(**new_data) ## pydantic obj
    data[p_id]=new_data.model_dump(exclude=["id"]) ## storing whole dictionary except id 
    save_data(data) 
    
    return JSONResponse(status_code=200,content={"message":"patient updated sucessfully"})

"""  ############### Alternative logic ####################
    old_data=data[p_id]
    new_data=patient.model_dump()

    for key,value in new_data.items():
        if value =="string" or value ==1 or value=="male":
            new_data[key]=old_data[key]


"""


@app.delete("/delete/{p_id}")
def delete_patient(p_id:str=Path(...,description="Enter id of patient to be deleted")):
    data=load_data()
    p_id=p_id.capitalize()
    if p_id not in data:
        raise HTTPException(status_code=400,detail="Patient not found")
    del data[p_id]
    save_data(data)
    return JSONResponse(status_code=200,content="Patient deleted sucessfully")



"""
********************** All routes *****************
@app.get("/")
@app.post('/create')
@app.get('/patient/{p_id}')
@app.get("/sort/{sort_by}/{order}")
@app.get("/sort") ## query parameter  localhost/sort?sort_by=height&order=desc
@app.put("/update/{p_id}")
@app.delete("/delete/{p_id}")

"""