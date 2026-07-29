import os
import json
import re
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

# Import components from existing project
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import AVAILABLE_TOOLS
from prompts import (
    REACT_SYSTEM_PROMPT, MAX_ITERATIONS,
    contains_crisis_signal, CRISIS_RESPONSE, is_valid_react_step, MALFORMED_OUTPUT_FALLBACK
)
from providers import get_llm_provider

load_dotenv()

app = FastAPI(title="VinUni ReAct Agent Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

async def generate_react_stream(user_query: str, provider):
    """Generator function that yields ReAct steps as Server-Sent Events."""
    
    # 1. Guardrail for crisis
    if contains_crisis_signal(user_query):
        yield {"data": json.dumps({"type": "crisis", "content": "⚠️ GUARDRAIL TRIGGERED: Phát hiện tín hiệu khủng hoảng!"})}
        await asyncio.sleep(0.5)
        yield {"data": json.dumps({"type": "final_answer", "content": CRISIS_RESPONSE})}
        return

    step = 0
    history = REACT_SYSTEM_PROMPT + f"\nUser: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        yield {"data": json.dumps({"type": "step_start", "content": f"--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---"})}
        
        # Run synchronous generation in threadpool to avoid blocking FastAPI
        response = await asyncio.to_thread(provider.generate, history)
        
        # 2. Guardrail for formatting
        if not is_valid_react_step(response):
            yield {"data": json.dumps({"type": "error", "content": "🛡️ GUARDRAIL TRIGGERED: LLM sinh sai định dạng."})}
            await asyncio.sleep(0.5)
            yield {"data": json.dumps({"type": "final_answer", "content": MALFORMED_OUTPUT_FALLBACK})}
            break
            
        history += response + "\n"
        
        # We want to show Thought and Action beautifully on frontend. 
        # Parse the response block manually or just send raw response block.
        yield {"data": json.dumps({"type": "llm_output", "content": response.strip()})}
        
        # 3. Check for Final Answer
        if "Final Answer:" in response:
            final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
            final_text = final_match.group(1).strip() if final_match else response
            yield {"data": json.dumps({"type": "final_answer", "content": final_text})}
            break
            
        # 4. Parse Action and execute Tool
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_args_str = action_match.group(2).strip()
            
            try:
                parsed_args = json.loads(tool_args_str)
                pretty_args = json.dumps(parsed_args, indent=2, ensure_ascii=False)
            except:
                pretty_args = tool_args_str
                
            yield {"data": json.dumps({"type": "tool_call", "tool_name": tool_name, "args": pretty_args})}
            
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    try:
                        args = json.loads(tool_args_str)
                        if isinstance(args, dict):
                            obs = tool_func(args)
                        else:
                            obs = tool_func(tool_args_str)
                    except json.JSONDecodeError:
                        obs = tool_func(tool_args_str)
                    
                    # Prettier JSON format for Observation
                    if isinstance(obs, (dict, list)):
                        obs_str = f"Observation:\n{json.dumps(obs, indent=2, ensure_ascii=False)}"
                    else:
                        obs_str = f"Observation: {obs}"
                except Exception as e:
                    obs_str = f"Observation: LỖI KHI GỌI TOOL - {str(e)}"
            else:
                obs_str = f"Observation: LỖI - Tool '{tool_name}' không tồn tại."
            
            yield {"data": json.dumps({"type": "observation", "content": obs_str})}
            history += obs_str + "\n"
        else:
            obs_str = "Observation: Vui lòng cung cấp 'Action:' hợp lệ hoặc 'Final Answer:'."
            yield {"data": json.dumps({"type": "observation", "content": obs_str})}
            history += obs_str + "\n"
            
    if step >= MAX_ITERATIONS:
        yield {"data": json.dumps({"type": "error", "content": f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!"})}

@app.get("/api/chat")
async def chat_endpoint(request: Request, q: str):
    provider = get_llm_provider()
    return EventSourceResponse(generate_react_stream(q, provider))
