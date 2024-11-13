from sqlalchemy import create_engine, Column, Integer, desc, asc, Boolean, Date, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from fastapi import FastAPI, status, Body
from fastapi.responses import FileResponse, JSONResponse

SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:poqw0912@localhost:5432/Lottery'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase): pass

class Data(Base):
    __tablename__ = "data"
 
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer)
    win_or_lost = Column(Boolean,default=False)
    lottery_date = Column(Date)

# создаем таблицы
Base.metadata.create_all(bind=engine)

# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()

app = FastAPI()

@app.get("/")
async def main():
    return FileResponse("public/lottery.html")

#Получение данных по последней лотерее
@app.get("/api/last_lottery")
def get_lastlottery():
    try:
        return db.query(Data).order_by(desc('lottery_date')).limit(80).all()
    except SQLAlchemyError as e:
        error = str(e)
        print(error)
        return error
    
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

#Создать новую лоттерею
@app.post("/api/create_lottery")
def insert_new_lottery(data_body = Body()):
    new_lottery = []
    numbers = data_body["nums"].split(' ')

    for i in numbers:
        new_lottery.append(Data(number = i,win_or_lost = data_body["is_won"],lottery_date = data_body["lottery_date"]))
    
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
            for r in results:
                data.append({
                    "number": r[0],
                    "count": r[1]
                })
        return JSONResponse(content=data, status_code=200)
    except SQLAlchemyError as e:
        error = str(e)
        return error
    
#Удалить определённую лотерею по дате
@app.post("/api/delete_lottery")
def delete_lottery(data_body = Body()):
    ltds = db.query(Data).filter(Data.lottery_date == data_body["lottery_date"]).all()
    print(ltds)
    if len(ltds) == 0:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={ "message": "No records on this date!" }
        )
    else:
        for i in ltds:
            db.delete(i)
        db.commit()