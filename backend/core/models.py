from __future__ import annotations
import os, time
from dataclasses import dataclass
from typing import Any

class ModelError(RuntimeError): pass

class BaseModel:
    name="base"; model_name="base"
    def generate(self,prompt): raise NotImplementedError
    def repair(self,prompt): raise NotImplementedError

@dataclass
class OpenAIAdapter(BaseModel):
    model_name: str = os.getenv("OPENAI_MODEL","gpt-5")
    name: str = "gpt"
    def __post_init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ModelError("OPENAI_API_KEY is not configured.")
        from openai import OpenAI
        self.client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    def _call(self,prompt):
        r=self.client.responses.create(model=self.model_name, input=prompt, max_output_tokens=1200, store=False)
        return r.output_text
    def generate(self,prompt): return self._call(prompt)
    def repair(self,prompt): return self._call(prompt)

@dataclass
class GeminiAdapter(BaseModel):
    model_name: str = os.getenv("GEMINI_MODEL","gemini-3.8-flash")
    name: str = "gemini"
    def __post_init__(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise ModelError("GEMINI_API_KEY is not configured.")
        from google import genai
        self.client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    def _call(self,prompt):
        r=self.client.models.generate_content(model=self.model_name, contents=prompt)
        return r.text or ""
    def generate(self,prompt): return self._call(prompt)
    def repair(self,prompt): return self._call(prompt)

class MockGPT(BaseModel):
    def __init__(self, name="gpt"):
        self.name=name; self.model_name=f"demo-mock-{name}"
    def generate(self,prompt):
        if "SystemVerilog" in prompt:
            return "```systemverilog\nmodule counter(input logic clk, input logic rst, output logic [3:0] count); always_ff @(posedge clk) begin if (rst) count <= 4'd0; else count <= count + 4'd1; end endmodule\n```"
        if "ODE" in prompt: return '{"solution":"exp(-x)"}'
        return '{"constraints":["x >= 0","y >= 0","x + y <= 10"],"claim":"x = 6 and y = 5"}'
    def repair(self,prompt):
        if "SystemVerilog" in prompt:
            return "module counter(input logic clk, input logic rst, output logic [3:0] count); always_ff @(posedge clk) begin if (rst) count <= 4'd0; else count <= count + 4'd1; end endmodule"
        if "ODE" in prompt: return '{"solution":"2*exp(-x)"}'
        return '{"constraints":["x >= 0","y >= 0","x + y <= 10"],"claim":"x = 5 and y = 5"}'

def available_models():
    out=[]
    if os.getenv("OPENAI_API_KEY"): out.append("gpt")
    if os.getenv("GEMINI_API_KEY"): out.append("gemini")
    return out

def build_model(name, allow_mock=False):
    if name=="gpt": return OpenAIAdapter() if os.getenv("OPENAI_API_KEY") else (MockGPT(name="gpt") if allow_mock else None)
    if name=="gemini": return GeminiAdapter() if os.getenv("GEMINI_API_KEY") else (MockGPT() if allow_mock else None)
    return None
