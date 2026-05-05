# FastAPI 官方文档精要

## 概述

FastAPI 是一个现代、高性能的 Python Web 框架，基于 Python 3.7+ 的类型提示构建 API。它基于 Starlette（Web 部分）和 Pydantic（数据验证），支持自动生成 OpenAPI 文档和异步处理。

### 安装与快速开始

```bash
pip install "fastapi[standard]"
```

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

运行：`fastapi dev main.py` 或 `uvicorn main:app --reload`

## 路径操作与请求

### 路径参数

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

类型提示自动完成数据验证和转换，无效类型返回 422 错误。

### 查询参数

```python
@app.get("/items/")
async def list_items(skip: int = 0, limit: int = 10, q: str | None = None):
    return {"skip": skip, "limit": limit, "q": q}
```

函数参数中不在路径中的参数自动成为查询参数。可选参数使用 `None` 默认值。

### 请求体

使用 Pydantic 模型定义请求体：

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

FastAPI 自动完成请求体的 JSON 解析、验证和文档生成。

### 表单与文件上传

```python
from fastapi import File, Form, UploadFile

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}

@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
```

## 依赖注入

FastAPI 的依赖注入系统是其最强大的特性之一：

```python
from fastapi import Depends

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

依赖可以嵌套、可以带 yield 实现清理逻辑（数据库连接关闭等）、可以是类实例。

### 安全与认证

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/users/me")
async def read_current_user(token: str = Depends(oauth2_scheme)):
    return {"token": token}
```

支持 OAuth2、JWT、HTTP Basic、API Key 等多种认证方式。

## 中间件与 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

自定义中间件：使用 `@app.middleware("http")` 装饰器或继承 `BaseHTTPMiddleware`。

## 后台任务与异步

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(message + "\n")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, f"notification sent to {email}")
    return {"message": "Notification sent"}
```

FastAPI 原生支持 async/await：如果使用 `async def`，会在线程池中运行；使用 `def` 则在线程池中运行以避免阻塞事件循环。

## 响应模型与状态码

```python
from fastapi import status

@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: Item) -> Item:
    return item
```

`response_model` 过滤输出数据，排除敏感字段（如密码）。支持 `response_model_exclude`、`response_model_include` 精确控制。

### 错误处理

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id < 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

自定义异常处理器：

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
```

## WebSocket 支持

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received: {data}")
```

## 最佳实践

1. **项目结构**：将路由、模型、服务分离到独立模块
2. **使用 Pydantic v2**：充分利用 model_validate、field_validator
3. **依赖注入管理数据库会话**：通过 yield 依赖自动处理事务
4. **利用 OpenAPI**：测试直接通过 `/docs` 交互式文档进行
5. **环境配置**：使用 pydantic-settings 管理多环境配置
