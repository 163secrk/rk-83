from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import appointments, technicians, parts, work_orders

Base.metadata.create_all(bind=engine)

app = FastAPI(title="汽车4S店售后保养预约系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments.router, prefix="/api/appointments", tags=["预约管理"])
app.include_router(technicians.router, prefix="/api/technicians", tags=["技师管理"])
app.include_router(parts.router, prefix="/api/parts", tags=["配件管理"])
app.include_router(work_orders.router, prefix="/api/work-orders", tags=["工单管理"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
