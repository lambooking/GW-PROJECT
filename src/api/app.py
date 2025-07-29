"""
FastAPI应用主文件
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
from pathlib import Path
from typing import List
import logging

from ..inference.audit_engine import AuditEngine
from ..inference.report_generator import ReportGenerator
from ..common.logger import setup_logger

# 设置日志
setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="生产运维管理AI审核系统",
    description="智能文档审核系统API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="output"), name="static")
except Exception as e:
    logger.warning(f"挂载静态文件目录失败: {e}")

# 初始化审核引擎和报告生成器
try:
    audit_engine = AuditEngine()
    report_generator = ReportGenerator()
except Exception as e:
    logger.error(f"初始化系统组件失败: {e}")
    audit_engine = None
    report_generator = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>生产运维管理AI审核系统</title>
        <style>
            body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .header { margin-bottom: 40px; }
            .api-list { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
            .api-item { margin: 15px 0; padding: 15px; background: rgba(255,255,255,0.2); border-radius: 10px; }
            .api-item h3 { margin: 0 0 10px 0; color: #fff; }
            .api-item p { margin: 0; opacity: 0.9; }
            a { color: #ffd700; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 生产运维管理AI审核系统</h1>
                <p>智能文档审核与质量评估平台</p>
            </div>
            
            <div class="api-list">
                <h2>📚 API接口文档</h2>
                <div class="api-item">
                    <a href="/docs">📖 Swagger UI - 交互式API文档</a>
                </div>
                <div class="api-item">
                    <a href="/redoc">📋 ReDoc - 详细API文档</a>
                </div>
                
                <h2>🚀 主要功能</h2>
                <div class="api-item">
                    <h3>📄 作业指导书审核</h3>
                    <p>POST /audit/instruction-book - 智能审核作业指导书文档</p>
                </div>
                <div class="api-item">
                    <h3>🏗️ 风险管控方案审核</h3>
                    <p>POST /audit/risk-management - 审核高后果区风险管控方案</p>
                </div>
                <div class="api-item">
                    <h3>📦 批量文档审核</h3>
                    <p>POST /audit/batch - 批量处理多个文档</p>
                </div>
                <div class="api-item">
                    <h3>💚 系统健康检查</h3>
                    <p>GET /health - 检查系统运行状态</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/audit/instruction-book")
async def audit_instruction_book(file: UploadFile = File(...)):
    """审核作业指导书"""
    if not audit_engine:
        raise HTTPException(status_code=500, detail="系统未正确初始化")
    
    try:
        # 检查文件格式
        if not file.filename.lower().endswith(('.docx', '.pdf', '.doc')):
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 .docx, .pdf 或 .doc 文件")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 进行审核
            logger.info(f"开始审核作业指导书: {file.filename}")
            audit_results = audit_engine.audit_instruction_book(temp_file_path)
            
            # 生成报告
            if report_generator:
                report_path = report_generator.generate_single_report(audit_results)
                report_url = f"/static/reports/{Path(report_path).name}"
            else:
                report_url = None
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
            return {
                "status": "success",
                "filename": file.filename,
                "results": audit_results,
                "report_url": report_url
            }
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"处理文件 {file.filename} 时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audit/risk-management")
async def audit_risk_management(file: UploadFile = File(...)):
    """审核高后果区风险管控方案"""
    if not audit_engine:
        raise HTTPException(status_code=500, detail="系统未正确初始化")
    
    try:
        # 检查文件格式
        if not file.filename.lower().endswith(('.docx', '.pdf', '.doc')):
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 .docx, .pdf 或 .doc 文件")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 进行审核
            logger.info(f"开始审核风险管控方案: {file.filename}")
            audit_results = audit_engine.audit_risk_management(temp_file_path)
            
            # 生成报告
            if report_generator:
                report_path = report_generator.generate_single_report(audit_results)
                report_url = f"/static/reports/{Path(report_path).name}"
            else:
                report_url = None
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
            return {
                "status": "success",
                "filename": file.filename,
                "results": audit_results,
                "report_url": report_url
            }
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"处理文件 {file.filename} 时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audit/batch")
async def batch_audit(files: List[UploadFile] = File(...)):
    """批量审核文档"""
    if not audit_engine:
        raise HTTPException(status_code=500, detail="系统未正确初始化")
    
    try:
        if len(files) > 50:  # 限制批量上传数量
            raise HTTPException(status_code=400, detail="批量上传文件数量不能超过50个")
        
        temp_files = []
        results = []
        
        try:
            # 保存所有临时文件
            for file in files:
                if not file.filename.lower().endswith(('.docx', '.pdf', '.doc')):
                    logger.warning(f"跳过不支持的文件格式: {file.filename}")
                    continue
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_files.append(temp_file.name)
            
            # 批量审核
            logger.info(f"开始批量审核 {len(temp_files)} 个文件")
            batch_results = audit_engine.batch_audit(temp_files, document_type='auto')
            
            # 生成批量报告
            if report_generator:
                report_path = report_generator.generate_batch_report(batch_results)
                report_url = f"/static/reports/{Path(report_path).name}"
                excel_url = f"/static/reports/{Path(report_path).stem}.xlsx"
            else:
                report_url = None
                excel_url = None
            
            return {
                "status": "success",
                "total_files": len(temp_files),
                "results": batch_results,
                "report_url": report_url,
                "excel_url": excel_url
            }
            
        finally:
            # 清理所有临时文件
            for temp_file_path in temp_files:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
    except Exception as e:
        logger.error(f"批量审核时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    status = {
        "status": "healthy" if audit_engine and report_generator else "degraded",
        "message": "AI审核系统运行正常" if audit_engine and report_generator else "部分组件未正确初始化",
        "components": {
            "audit_engine": "ok" if audit_engine else "error",
            "report_generator": "ok" if report_generator else "error"
        }
    }
    return status


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 