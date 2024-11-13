from sqlalchemy import create_engine, Column, Integer, desc, asc, Boolean, Date, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from fastapi import FastAPI, status, Body
from fastapi.responses import FileResponse, JSONResponse

#My Local database
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:poqw0912@localhost:5432/Lottery'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase): pass

#Initiate a data base table
class Data(Base):
    __tablename__ = "data"
 
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer)
    win_or_lost = Column(Boolean,default=False)
    lottery_date = Column(Date)

#Create table
Base.metadata.create_all(bind=engine)

#Create session to connect to a teble
SessionLocal = sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()

app = FastAPI()

#Loading lottery.html page
@app.get("/")
async def main():
    return FileResponse("public/lottery.html")

#Get data on a last lottery
@app.get("/api/last_lottery")
def get_lastlottery():
    try:
        return db.query(Data).order_by(desc('lottery_date')).limit(80).all()
    except SQLAlchemyError as e:
        error = str(e)
        return error

#Get lottery data by date    
@app.get("/api/get_lottery_by_date/{lotDate}")
def get_lottery_by_date(lotDate):
    ltds = db.query(Data).filter(Data.lottery_date == lotDate).all()
    if len(ltds) == 0:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={ "message": "No records on this date!" }
        )
    else:
        return ltds

#Create new lottery
@app.post("/api/create_lottery")
def insert_new_lottery(data_body = Body()):
    new_lottery = []
    numbers = data_body["nums"].split(' ')

    [new_lottery.append(Data(number = i,win_or_lost = data_body["is_won"],lottery_date = data_body["lottery_date"])) for i in numbers]
    
    try:
        db.add_all(new_lottery)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.orig)
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={ "message": error }
        )

#Get lottery results in to table
@app.get("/api/get_lottery_results")
def get_lottery_results():
    query = (
        db.query(Data.number, func.count().label('count'))
        .filter(Data.win_or_lost == False)
        .group_by(Data.number)
        .having(func.count() <= 17)
        .order_by(asc(func.count())) 
        ) 

    try:
        results = query.all()
        if results:
            data = []
            [data.append({"number": r[0], "count": r[1]}) for r in results]
        return JSONResponse(content=data, status_code=200)
    except SQLAlchemyError as e:
        error = str(e)
        return error
    
#Delete lottery data by date
@app.post("/api/delete_lottery")
def delete_lottery(data_body = Body()):
    ltds = db.query(Data).filter(Data.lottery_date == data_body["lottery_date"]).all()
    if len(ltds) == 0:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={ "message": "No records on this date!" }
        )
    else:
        [db.delete(i) for i in ltds]
        db.commit()