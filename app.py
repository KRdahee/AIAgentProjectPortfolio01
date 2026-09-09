from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uvicorn
import traceback

from workflow import run_pipeline

app = FastAPI(title="사내 기획서 자동 검토 시스템")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ProposalDraft(BaseModel):
    title: str
    purpose: str
    target: str
    content: str
    expected_effect: str

class ReviewFeedback(BaseModel):
    is_approved: bool
    feedback: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request}
    )

@app.post("/api/run_workflow")
async def run_workflow(draft: ProposalDraft):
    try:
        # Pydantic v2 호환성을 위해 model_dump() 사용 (또는 dict())
        draft_dict = draft.dict() if hasattr(draft, 'dict') else draft.model_dump()
        result_data = await run_pipeline(draft_dict)
        return JSONResponse(content=result_data)

    except Exception as e:
        # 터미널에 상세 에러 로그(Traceback)를 출력하여 디버깅을 돕습니다.
        error_msg = f"서버 내부 오류: {str(e)}"
        print("="*50)
        print("[서버 500 에러 상세 내역]")
        traceback.print_exc()
        print("="*50)
        return JSONResponse(status_code=500, content={"error": error_msg})

@app.post("/api/resume_workflow")
async def resume_workflow(review: ReviewFeedback):
    if review.is_approved:
        return {"status": "approved", "docx_path": "/static/downloads/proposal_final.docx"}
    else:
        return {"status": "rejected", "message": f"반려 사유 반영 완료: {review.feedback}"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)