from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
from typing import List, Optional
import json
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import aiofiles
from pathlib import Path
import base64
import fitz  # PyMuPDF
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="PDF Table Extractor API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/pdf_extractor")
client = AsyncIOMotorClient(MONGO_URL)
db = client.pdf_extractor

# Upload folder
UPLOAD_FOLDER = Path("./uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Pydantic models
class FileInfo(BaseModel):
    file_id: str
    filename: str
    uploaded_at: datetime
    total_pages: int
    file_size: int

class TableSelection(BaseModel):
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float

class ExtractionJob(BaseModel):
    job_id: str
    file_id: str
    selections: List[TableSelection]
    created_at: datetime
    status: str = "pending"
    csv_data: Optional[str] = None

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Validate file size (limit to 50MB)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="File size too large. Maximum 50MB allowed")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save file
        file_path = UPLOAD_FOLDER / f"{file_id}_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Get PDF info using PyMuPDF
        try:
            pdf_doc = fitz.open(file_path)
            total_pages = len(pdf_doc)
            pdf_doc.close()
        except Exception as e:
            # Clean up the file if PDF is invalid
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=f"Invalid PDF file: {str(e)}")
        
        # Save file info to database
        file_info = {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "uploaded_at": datetime.now(),
            "total_pages": total_pages,
            "file_size": len(content)
        }
        
        try:
            await db.files.insert_one(file_info)
        except Exception as e:
            # Clean up the file if database insert fails
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "total_pages": total_pages,
            "file_size": len(content)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch all other exceptions
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    try:
        file_info = await db.files.find_one({"file_id": file_id})
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert ObjectId to string for JSON serialization
        file_info["_id"] = str(file_info["_id"])
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/files/{file_id}/pdf")
async def get_pdf_file(file_id: str):
    try:
        file_info = await db.files.find_one({"file_id": file_id})
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(file_info["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=file_info["filename"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/api/extract")
async def extract_tables(
    file_id: str = Form(...),
    selections: str = Form(...)
):
    try:
        # Parse selections
        try:
            selections_data = json.loads(selections)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid selections format")
        
        # Get file info
        file_info = await db.files.find_one({"file_id": file_id})
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(file_info["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Extract tables from selected areas
        csv_data = await extract_tables_from_selections(file_path, selections_data)
        
        # Create extraction job
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "file_id": file_id,
            "selections": selections_data,
            "created_at": datetime.now(),
            "status": "completed",
            "csv_data": csv_data
        }
        
        await db.jobs.insert_one(job)
        
        return {
            "job_id": job_id,
            "status": "completed",
            "csv_data": csv_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

async def extract_tables_from_selections(file_path: Path, selections: List[dict]) -> str:
    """Extract tables from PDF based on manual selections"""
    try:
        # Open PDF
        pdf_doc = fitz.open(file_path)
        
        all_tables = []
        
        for selection in selections:
            page_num = selection["page"]
            x1, y1, x2, y2 = selection["x1"], selection["y1"], selection["x2"], selection["y2"]
            
            # Get page
            page = pdf_doc[page_num]
            
            # Define rectangle area
            rect = fitz.Rect(x1, y1, x2, y2)
            
            # Extract text from the selected area
            text = page.get_text("text", clip=rect)
            
            # Simple text-to-table conversion (this is a basic implementation)
            lines = text.strip().split('\n')
            table_data = []
            
            for line in lines:
                if line.strip():
                    # Split by whitespace (basic approach)
                    row = [cell.strip() for cell in line.split() if cell.strip()]
                    if row:
                        table_data.append(row)
            
            if table_data:
                # Convert to DataFrame and then to CSV
                max_cols = max(len(row) for row in table_data)
                
                # Pad rows to have same number of columns
                for row in table_data:
                    while len(row) < max_cols:
                        row.append("")
                
                df = pd.DataFrame(table_data)
                all_tables.append(df)
        
        pdf_doc.close()
        
        # Combine all tables
        if all_tables:
            combined_df = pd.concat(all_tables, ignore_index=True)
            return combined_df.to_csv(index=False)
        else:
            return "No data extracted"
            
    except Exception as e:
        raise Exception(f"Error extracting tables: {str(e)}")

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        job = await db.jobs.find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job["_id"] = str(job["_id"])
        return job
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/download")
async def download_csv(job_id: str):
    try:
        job = await db.jobs.find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if not job.get("csv_data"):
            raise HTTPException(status_code=404, detail="No CSV data available")
        
        # Create temporary CSV file
        csv_file_path = UPLOAD_FOLDER / f"{job_id}_extracted.csv"
        
        async with aiofiles.open(csv_file_path, 'w') as f:
            await f.write(job["csv_data"])
        
        return FileResponse(
            csv_file_path,
            media_type="text/csv",
            filename=f"extracted_tables_{job_id}.csv"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)