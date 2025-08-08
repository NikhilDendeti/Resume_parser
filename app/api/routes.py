# import asyncio
# import time
# import uuid
# from datetime import datetime
# from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
# from fastapi.responses import JSONResponse
# from typing import Optional

# from ..models.resume_models import ParseResponse, JobStatus, ParsedResume
# from ..services.text_extractor import TextExtractor
# from ..services.rule_based_parser import RuleBasedParser
# from ..services.llm_parser import LLMParser
# from ..config import settings

# router = APIRouter()

# # Initialize services
# text_extractor = TextExtractor()
# rule_parser = RuleBasedParser()
# llm_parser = LLMParser()

# @router.post("/parse", response_model=ParseResponse)
# async def parse_resume_sync(
#     file: UploadFile = File(...),
#     use_llm_fallback: bool = True,
#     llm_provider: str = "openai"
# ):
#     """
#     Synchronous resume parsing endpoint
#     """
#     try:
#         # Validate file
#         if not file.filename:
#             raise HTTPException(status_code=400, detail="No file provided")
        
#         file_extension = file.filename.split('.')[-1].lower()
#         if file_extension not in settings.SUPPORTED_FORMATS:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Unsupported file format. Supported: {settings.SUPPORTED_FORMATS}"
#             )
        
#         # Read file content
#         file_content = await file.read()
#         if len(file_content) > settings.MAX_FILE_SIZE:
#             raise HTTPException(status_code=413, detail="File too large")
        
#         start_time = time.time()
        
#         # Extract text
#         text, extraction_method = await text_extractor.extract_text(
#             file_content, file.filename
#         )
        
#         if not text.strip():
#             raise HTTPException(status_code=400, detail="No text could be extracted from file")
        
#         # Check cache
#         cached_result = await cache_service.get_cached_result(text)
#         if cached_result:
#             cached_result['processing_time'] = time.time() - start_time
#             return ParseResponse(success=True, data=ParsedResume.model_validate(cached_result))
        
#         # Try rule-based parsing first
#         parsed_resume, confidence = rule_parser.parse(text)
        
#         # Use LLM fallback if confidence is low
#         if confidence < settings.RULE_CONFIDENCE_THRESHOLD and use_llm_fallback:
#             try:
#                 llm_resume, llm_confidence = await llm_parser.parse(text, llm_provider)
#                 if llm_confidence > confidence:
#                     parsed_resume = llm_resume
#             except Exception as e:
#                 print(f"LLM fallback failed: {e}")
#                 # Continue with rule-based result
        
#         # Set processing time
#         parsed_resume.processing_time = time.time() - start_time
        
#         # Cache result
#         await cache_service.cache_result(text, parsed_resume.model_dump())
        
#         return ParseResponse(success=True, data=parsed_resume)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         return ParseResponse(
#             success=False,
#             error=f"Processing failed: {str(e)}"
#         )

# @router.post("/parse/async", response_model=ParseResponse)
# async def parse_resume_async(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     use_llm_fallback: bool = True,
#     llm_provider: str = "openai"
# ):
#     """
#     Asynchronous resume parsing endpoint
#     """
#     try:
#         # Validate file
#         if not file.filename:
#             raise HTTPException(status_code=400, detail="No file provided")
        
#         file_extension = file.filename.split('.')[-1].lower()
#         if file_extension not in settings.SUPPORTED_FORMATS:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Unsupported file format. Supported: {settings.SUPPORTED_FORMATS}"
#             )
        
#         # Read file content
#         file_content = await file.read()
#         if len(file_content) > settings.MAX_FILE_SIZE:
#             raise HTTPException(status_code=413, detail="File too large")
        
#         # Generate job ID
#         job_id = str(uuid.uuid4())
        
#         # Store initial job status
#         await cache_service.store_job_status(job_id, {
#             "job_id": job_id,
#             "status": "pending",
#             "created_at": datetime.now().isoformat()
#         })
        
#         # Add background task
#         background_tasks.add_task(
#             process_resume_async,
#             job_id,
#             file_content,
#             file.filename,
#             use_llm_fallback,
#             llm_provider
#         )
        
#         return ParseResponse(
#             success=True,
#             job_id=job_id
#         )
        
#     except Exception as e:
#         return ParseResponse(
#             success=False,
#             error=f"Failed to queue job: {str(e)}"
#         )

# @router.get("/job/{job_id}", response_model=JobStatus)
# async def get_job_status(job_id: str):
#     """
#     Get job status for async processing
#     """
#     try:
#         status = await cache_service.get_job_status(job_id)
#         if not status:
#             raise HTTPException(status_code=404, detail="Job not found")
        
#         return JobStatus.model_validate(status)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

# @router.get("/health")
# async def health_check():

#     return {"status": "ok"}



import asyncio
import time
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional

from ..models.resume_models import ParseResponse, JobStatus, ParsedResume
from ..services.text_extractor import TextExtractor
from ..services.rule_based_parser import RuleBasedParser
from ..services.llm_parser import LLMParser
from ..config import settings

router = APIRouter()

# Initialize services
text_extractor = TextExtractor()
rule_parser = RuleBasedParser()
llm_parser = LLMParser()

@router.post("/parse", response_model=ParseResponse)
async def parse_resume_sync(
    file: UploadFile = File(...),
    use_llm_fallback: bool = True,
    llm_provider: str = "openai"
):
    """
    Synchronous resume parsing endpoint
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {settings.SUPPORTED_FORMATS}"
            )
        
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        start_time = time.time()
        
        text, extraction_method = await text_extractor.extract_text(
            file_content, file.filename
        )
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from file")
        
        parsed_resume, confidence = rule_parser.parse(text)
        
        if confidence < settings.RULE_CONFIDENCE_THRESHOLD and use_llm_fallback:
            try:
                llm_resume, llm_confidence = await llm_parser.parse(text, llm_provider)
                if llm_confidence > confidence:
                    parsed_resume = llm_resume
            except Exception as e:
                print(f"LLM fallback failed: {e}")
        
        parsed_resume.processing_time = time.time() - start_time
        
        return ParseResponse(success=True, data=parsed_resume)
        
    except HTTPException:
        raise
    except Exception as e:
        return ParseResponse(
            success=False,
            error=f"Processing failed: {str(e)}"
        )

@router.post("/parse/async", response_model=ParseResponse)
async def parse_resume_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_llm_fallback: bool = True,
    llm_provider: str = "openai"
):
    """
    Asynchronous resume parsing endpoint (without cache)
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {settings.SUPPORTED_FORMATS}"
            )
        
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        job_id = str(uuid.uuid4())

        # Add background task (you need to implement `process_resume_async` somewhere)
        background_tasks.add_task(
            process_resume_async,
            job_id,
            file_content,
            file.filename,
            use_llm_fallback,
            llm_provider
        )
        
        return ParseResponse(
            success=True,
            job_id=job_id
        )
        
    except Exception as e:
        return ParseResponse(
            success=False,
            error=f"Failed to queue job: {str(e)}"
        )

@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Dummy job status endpoint (since caching is removed)
    """
    raise HTTPException(status_code=410, detail="Async job status tracking has been disabled")

@router.get("/health")
async def health_check():
    return {"status": "ok"}
