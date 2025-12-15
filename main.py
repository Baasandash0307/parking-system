from fastapi import FastAPI, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
import crud
import easyocr
import cv2
import numpy as np
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# OCR reader
reader = easyocr.Reader(["mn"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def extract_plate_from_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    results = reader.readtext(image)

    if results:
        results = sorted(results, key=lambda x: x[2], reverse=True)
        for detection in results:
            text = detection[1]
            confidence = detection[2]
            plate = text.upper().replace(" ", "").replace("-", "")
            if len(plate) >= 4 and confidence > 0.5:
                return plate
    return None


# --- Орсон машинуудыг шалгах логик нэмсэн --- #


@app.post("/enter-with-image")
async def enter_car_with_image(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        image_bytes = await file.read()
        plate = extract_plate_from_image(image_bytes)

        if not plate:
            return {"error": "Машины дугаар олдсонгүй"}

        vehicle = crud.get_vehicle_by_plate(db, plate)
        if not vehicle:
            vehicle = crud.create_vehicle(db, plate)

        log = crud.vehicle_enter(db, vehicle)
        if not log:
            return {
                "error": f"Машин ({plate}) аль хэдийн зогсоолд байна",
                "plate": plate,
            }

        return {"message": f"Машин орлоо", "plate": plate, "entered_at": log.entered_at}

    except Exception as e:
        return {"error": f"Алдаа гарлаа: {str(e)}"}


@app.post("/enter")
def enter_car(plate: str, db: Session = Depends(get_db)):
    vehicle = crud.get_vehicle_by_plate(db, plate)
    if not vehicle:
        vehicle = crud.create_vehicle(db, plate)

    log = crud.vehicle_enter(db, vehicle)
    if not log:
        return {"error": f"{plate} дугаартай машин аль хэдийн зогсоолд байна"}

    return {"message": "Машин орлоо", "entered_at": log.entered_at}


# --- Гарч байгаа endpoint --- #
@app.post("/exit")
def exit_car(plate: str, db: Session = Depends(get_db)):
    vehicle = crud.get_vehicle_by_plate(db, plate)
    if not vehicle:
        return {"error": "Машин олдсонгүй"}

    log = crud.vehicle_exit(db, vehicle)
    if not log:
        return {"error": "Зогсоолд байхгүй машин байна"}

    minutes = crud.calculate_minutes(log)
    fee = crud.calculate_fee(minutes)

    return {
        "message": f"Машин гарлаа",
        "entered_at": log.entered_at,
        "exited_at": log.exited_at,
        "minutes": minutes,
        "fee": fee,
    }


# --- Зогсоолд байгаа машинуудыг авах --- #
@app.get("/parked-vehicles")
def get_parked_vehicles(db: Session = Depends(get_db)):
    # Орон нутгийн цагийг ашигла
    current_time = datetime.now()  # datetime.utcnow() биш
    parked_vehicles = crud.get_all_parked_vehicles(db)

    result = []
    for vehicle, log in parked_vehicles:
        delta = current_time - log.entered_at
        minutes = int(delta.total_seconds() / 60)
        fee = crud.calculate_fee(minutes)
        result.append(
            {
                "plate": vehicle.plate_number,
                "entered_at": log.entered_at,
                "minutes_parked": minutes,
                "current_fee": fee,
            }
        )
    return {"total": len(result), "vehicles": result}


# --- Машины дугаарыг зөвхөн таних --- #
@app.post("/detect-plate")
async def detect_plate_only(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        plate = extract_plate_from_image(image_bytes)
        if not plate:
            return {"error": "Машины дугаар олдсонгүй", "plate": None}
        return {"plate": plate, "message": "Амжилттай танилаа"}
    except Exception as e:
        return {"error": f"Алдаа гарлаа: {str(e)}", "plate": None}
