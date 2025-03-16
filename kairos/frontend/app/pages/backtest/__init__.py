"""
백테스트 페이지 모듈
"""
from .run import render as render_run

pages = {
    "run": render_run
}

def render(page_name="run"):
    """
    백테스트 페이지 렌더링
    
    Args:
        page_name: 페이지 이름 (기본값: "run")
    """
    if page_name in pages:
        return pages[page_name]()
    else:
        return pages["run"]() 