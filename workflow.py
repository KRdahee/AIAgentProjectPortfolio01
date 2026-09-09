import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .env 파일에서 환경변수 로드
load_dotenv()

# 최신 google-genai 클라이언트 초기화 (환경변수 GEMINI_API_KEY 자동 감지)
client = genai.Client()
MODEL_ID = 'gemini-3.6-flash'

def clean_json_text(text: str) -> str:
    """AI 응답 텍스트에서 마크다운 백틱(```json ... ```) 제거"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def run_pipeline(draft_data: dict):
    try:
        # 1. Analyzer Agent: 완성도 진단
        analyzer_prompt = f"""
        당신은 엄격하고 논리적인 공기업 기획팀 수석 심사역입니다.
        제출된 기획서 초안을 분석하여 반드시 아래 JSON 형식으로만 결과를 반환하세요. (다른 설명이나 마크다운 백틱 사용 금지)
        초안 데이터: {draft_data}
        
        출력 양식(JSON):
        {{
            "score": 85,
            "missing_items": ["누락항목1", "누락항목2"],
            "improvement_direction": "핵심 개선 방향 요약"
        }}
        """
        resp_analyzer = client.models.generate_content(
            model=MODEL_ID,
            contents=analyzer_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        analysis_result = json.loads(clean_json_text(resp_analyzer.text))

        # 2. Enhancer Agent: SWOT 및 정량 지표 보완
        enhancer_prompt = f"""
        당신은 통찰력 있는 공기업 전략 기획가입니다.
        기획서 초안을 바탕으로 2x2 SWOT 분석과 가상의 정량적 목표 지표를 도출해 반드시 아래 JSON 형식으로만 반환하세요.
        초안 데이터: {draft_data}
        
        출력 양식(JSON):
        {{
            "swot": {{
                "strengths": ["강점1"],
                "weaknesses": ["약점1"],
                "opportunities": ["기회1"],
                "threats": ["위협1"]
            }},
            "metrics": "□ 주요 정량 목표\\n  - 지표1: 수치\\n  - 지표2: 수치"
        }}
        """
        resp_enhancer = client.models.generate_content(
            model=MODEL_ID,
            contents=enhancer_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        enhancer_result = json.loads(clean_json_text(resp_enhancer.text))

        # 3. Converter Agent: 공기업 표준 개조식 변환
        converter_prompt = f"""
        당신은 공기업 기획팀의 문서 작성 전문가입니다.
        주어진 초안을 공공기관에서 사용하는 완벽한 '3단 개조식 양식(1. 추진 배경 및 목적, 2. 주요 사업 내용, 3. 기대효과)'으로 변환하세요.
        반드시 '~함', '~구축', '~운영' 등 명사형 종결어미와 계층적 기호(□, ○, -)를 사용하고, 반드시 아래 JSON 형식으로만 반환하세요.
        초안 데이터: {draft_data}
        
        출력 양식(JSON):
        {{
            "converted": "개조식으로 변환된 텍스트"
        }}
        """
        resp_converter = client.models.generate_content(
            model=MODEL_ID,
            contents=converter_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        converter_result = json.loads(clean_json_text(resp_converter.text))

        return {
            "analysis": analysis_result,
            "swot": enhancer_result.get("swot", {}),
            "metrics": enhancer_result.get("metrics", "지표 도출 실패"),
            "converted": converter_result.get("converted", "변환 실패")
        }
        
    except Exception as e:
        print(f"[-] 최신 SDK 파이프라인 구동 중 에러 발생: {str(e)}")
        raise e