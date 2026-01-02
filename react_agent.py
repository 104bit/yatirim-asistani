"""
ReAct Agent v4 - With Reflection
=================================
Tool use + Reflection for better quality outputs.
"""

import os
import time
import json
import re
from typing import TypedDict
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from tools.market_tools import ALL_TOOLS

# Rate limit delay
RATE_LIMIT_DELAY = 2


# =============================================================================
# STATE
# =============================================================================
class AgentState(TypedDict):
    messages: list
    user_query: str
    tool_results: dict
    iteration: int
    draft_answer: str
    final_report: str
    needs_more_work: bool


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
REACT_SYSTEM_PROMPT = """Sen Türkiye'nin en iyi Finansal Araştırma Ajansısın.

## TEMEL PRENSİPLER
1. **SOMUT VERİ** → Her raporda fiyat, değişim, RSI gibi sayılar olmalı
2. **ARAŞTIR, UYDURMA** → Veri bulamazsan açıkça söyle, asla tahmin etme
3. **PROAKTİF OL** → Belirsiz sorularda bile araştır, pasif kalma
4. **NİYETİ ANLA** → Kullanıcının gerçek amacını çöz, en uygun tool'u seç

## ARAÇLARIN
| Araç | Ne Zaman Kullan |
|------|-----------------|
| analyze_stock(x) | Spesifik varlık analizi (altın, bitcoin, THYAO vb.) |
| get_news(x) | Haber ve sentiment için |
| scan_sector(x) | Sektör karşılaştırması (banka, holding, enerji) |
| web_search(x) | Belirsiz sorgular, geçmiş veriler, trend araştırması |
| compare([x,y]) | 2-3 varlık karşılaştırması |
| get_forex(x) | Döviz kurları (USDTRY, EURTRY) |

## ARAÇ ÇAĞIRMA
<tool>araç_adı("parametre")</tool> formatını kullan. Max 3 araç.

## ÖRNEK KARARLAR (Bunlardan öğren!)

### ✅ Spesifik Varlık Sorusu
Soru: "Bakır alınır mı?"
→ analyze_stock("bakır") + get_news("bakır")

### ✅ Belirsiz/Genel Soru  
Soru: "Ne alayım?" veya "Zengin olmak istiyorum"
→ web_search("en iyi yatırım 2026") + scan_sector("holding") + analyze_stock("altın")
→ Sonra çeşitlendirilmiş portföy öner

### ✅ Geçmiş Tarihli Soru
Soru: "2024'te hangi hisseler kazandırdı?"
→ web_search("2024 en çok kazandıran hisseler Türkiye")

### ✅ Gelecek Tahmini
Soru: "2030'da Bitcoin ne olur?"
→ analyze_stock("bitcoin") + get_news("bitcoin")
→ Mevcut veriyi ver + "⚠️ Gelecek tahminleri kesin değildir" disclaimer ekle

### ✅ Sektör Sorusu
Soru: "Banka sektörü nasıl?"
→ scan_sector("banka")

### ❌ Fantezi/İmkansız Soru
Soru: "Mars'taki altın madeni hissesi?"
→ Tool çağırma! Cevap: "Bu gerçek bir finansal varlık değil."

### ❌ Anlamsız Sorgu
Soru: "asdfghjkl" veya sadece "yatırım"
→ Tool çağırma! Cevap: "Lütfen spesifik bir varlık veya soru belirtin."

## RAPOR FORMATI
Her raporda şunlar olmalı:
- 📊 Fiyat ve teknik veriler
- 📰 Güncel haberler ve sentiment
- 💡 Net tavsiye (AL/SAT/TUT) + gerekçe
"""

REFLECTION_PROMPT = """Aşağıdaki cevabı değerlendir:

KULLANICI SORUSU: {query}

MEVCUT CEVAP:
{answer}

## DEĞERLENDİRME KRİTERLERİ

### KABUL EDİLEBİLİR CEVAPLAR:

**Senaryo A - Veri ile cevap:**
1. ✅ Somut FİYAT değeri var mı? (örn: "4.52 USD", "23.82 TL")
2. ✅ DEĞİŞİM yüzdesi var mı? (örn: "+2.1%", "-0.7%")
3. ✅ Net TAVSİYE var mı? (AL/SAT/TUT veya Türkçe karşılığı)
4. ✅ HABER/SENTİMENT bilgisi var mı?

**Senaryo B - Geçerli RED cevabı:**
- "bulunamadı", "mevcut değil", "geçerli değil" ifadesi var mı?
- Fantezi/hayali sorgu reddi var mı? (Mars, gelecek tahmini yapılamaz vb.)
- "Bu sorgu gerçek bir finansal varlık içermiyor" gibi açıklama var mı?

## KARAR
- Senaryo A veya Senaryo B karşılanıyorsa → "TAMAM" yaz
- Her iki senaryo da karşılanmıyorsa → "DEVAM: analyze_stock çağır" yaz

Sadece TAMAM veya DEVAM: yazısıyla cevap ver, başka bir şey yazma.
"""


# =============================================================================
# QUERY REWRITER PROMPT (Pre-LLM)
# =============================================================================
QUERY_REWRITER_PROMPT = """Kullanıcının sorusunu analiz et ve agent için yeniden yaz.

SORU: {query}

## ANALİZ ET:
1. ZAMAN: Geçmiş (2024, geçen yıl) / Şimdi / Gelecek (2030, 5 yıl sonra)?
2. VARLIK: Spesifik (altın, bitcoin, THY) / Genel (ne alayım)?
3. TİP: Analiz / Karşılaştırma / Sektör / Araştırma?

## TOOL ÖNERİSİ:
- Geçmiş veri → web_search("... [yıl] en iyi performans")
- Spesifik varlık → analyze_stock + get_news
- Genel soru → web_search + scan_sector + analyze_stock
- Sektör → scan_sector
- Karşılaştırma → compare

## ÇIKTI FORMATI:
Soruyu şu şekilde yeniden yaz:
"[Orijinal niyet]. [Kullanılacak tool'lar: tool1, tool2]"

Örnek:
- "2024 hisseler" → "2024 yılında en çok kazandıran BIST hisselerini araştır. [web_search kullan]"
- "altın mı bitcoin mi" → "Altın ve Bitcoin'i karşılaştır. [compare veya analyze_stock x2 kullan]"
- "ne alayım" → "Yatırım önerisi için güncel trendleri araştır. [web_search + scan_sector + analyze_stock kullan]"

Sadece yeniden yazılmış sorguyu döndür, başka açıklama yapma.
"""


def rewrite_query(user_query: str) -> str:
    """Pre-LLM: Kullanıcı sorgusunu analiz et ve agent için optimize et."""
    print(f"\n[🔄 Query Rewriter] Analyzing: {user_query}")
    
    try:
        llm = get_llm()
        prompt = QUERY_REWRITER_PROMPT.format(query=user_query)
        response = llm.invoke([HumanMessage(content=prompt)])
        rewritten = response.content.strip()
        
        print(f"[🔄 Query Rewriter] Rewritten: {rewritten}")
        return rewritten
    except Exception as e:
        print(f"[🔄 Query Rewriter] Error: {e}, using original query")
        return user_query


# =============================================================================
# LLM SETUP
# =============================================================================
def get_llm():
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if openrouter_key:
        return ChatOpenAI(
            model="openai/gpt-4o-mini-2024-07-18",
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "FinAgent"
            }
        )
    elif google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_key,
            temperature=0.3
        )
    else:
        raise ValueError("No API key")


# =============================================================================
# TOOL EXECUTOR
# =============================================================================
def execute_tool(tool_call: str) -> str:
    match = re.match(r'(\w+)\((.*)\)', tool_call.strip())
    if not match:
        return f"Invalid tool call: {tool_call}"
    
    tool_name = match.group(1)
    args_str = match.group(2)
    
    tool_fn = next((t for t in ALL_TOOLS if t.name == tool_name), None)
    if not tool_fn:
        return f"Tool not found: {tool_name}"
    
    try:
        if args_str.startswith('['):
            args = {"symbols": json.loads(args_str)}
        elif args_str.startswith('"') or args_str.startswith("'"):
            args = json.loads(f'{{"arg": {args_str}}}')
            args = {list(tool_fn.args.keys())[0]: args["arg"]}
        elif ',' in args_str:
            parts = args_str.split(',', 1)
            args = {
                "amount": float(parts[0].strip()),
                "symbols": json.loads(parts[1].strip())
            }
        else:
            args = {list(tool_fn.args.keys())[0]: args_str.strip().strip('"').strip("'")}
        
        result = tool_fn.invoke(args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# AGENT NODE
# =============================================================================
def agent_node(state: AgentState) -> AgentState:
    print("\n[Agent] Thinking...")
    time.sleep(RATE_LIMIT_DELAY)
    
    llm = get_llm()
    messages = state["messages"]
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=REACT_SYSTEM_PROMPT)] + messages
    
    # Add tool results if any
    if state.get("tool_results"):
        results_msg = "\n\nARAÇ SONUÇLARI:\n"
        for tool, result in state["tool_results"].items():
            results_msg += f"{tool}: {result}\n"
        results_msg += "\nBu verilere göre detaylı rapor yaz. Sayısal veriler ve net tavsiye ver."
        messages = messages + [HumanMessage(content=results_msg)]
        state["tool_results"] = {}
    
    # Check if reflection said to continue
    if state.get("needs_more_work"):
        messages = messages + [HumanMessage(content="Cevabın yetersiz bulundu. Daha fazla veri topla ve analiz yap.")]
        state["needs_more_work"] = False
    
    response = llm.invoke(messages)
    state["messages"] = messages + [response]
    state["iteration"] = state.get("iteration", 0) + 1
    
    content = response.content
    tool_matches = re.findall(r'<tool>(.*?)</tool>', content, re.DOTALL)
    
    if tool_matches and state["iteration"] < 5:
        print(f"[Agent] Found {len(tool_matches)} tool calls")
        for tm in tool_matches:
            print(f"  → {tm}")
    else:
        print("[Agent] Draft answer ready → Reflection")
        clean_content = re.sub(r'<tool>.*?</tool>', '', content, flags=re.DOTALL).strip()
        state["draft_answer"] = clean_content
    
    return state


# =============================================================================
# TOOL NODE
# =============================================================================
def tool_node(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    content = last.content if hasattr(last, 'content') else str(last)
    
    tool_matches = re.findall(r'<tool>(.*?)</tool>', content, re.DOTALL)
    
    results = {}
    for tm in tool_matches[:3]:
        print(f"[Tool] Executing: {tm}")
        results[tm] = execute_tool(tm)
    
    state["tool_results"] = results
    return state


# =============================================================================
# REFLECTION NODE
# =============================================================================
def reflection_node(state: AgentState) -> AgentState:
    print("\n[🪞 Reflection] Evaluating answer quality...")
    time.sleep(RATE_LIMIT_DELAY)
    
    llm = get_llm()
    
    prompt = REFLECTION_PROMPT.format(
        query=state["user_query"],
        answer=state["draft_answer"]
    )
    
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    
    print(f"[🪞 Reflection] Result: {result[:50]}...")
    
    if "TAMAM" in result.upper():
        print("[🪞 Reflection] ✅ Answer approved!")
        state["final_report"] = state["draft_answer"]
    else:
        print("[🪞 Reflection] ⚠️ Needs more work...")
        state["needs_more_work"] = True
        state["draft_answer"] = ""
    
    return state


# =============================================================================
# ROUTING
# =============================================================================
def should_continue(state: AgentState) -> str:
    if state.get("final_report"):
        return "end"
    
    if state.get("draft_answer"):
        return "reflect"
    
    last = state["messages"][-1]
    content = last.content if hasattr(last, 'content') else ""
    
    if '<tool>' in content and state.get("iteration", 0) < 5:
        return "tools"
    
    # No tools, no draft - treat as draft
    state["draft_answer"] = content
    return "reflect"


def after_reflection(state: AgentState) -> str:
    if state.get("final_report"):
        return "end"
    if state.get("needs_more_work") and state.get("iteration", 0) < 5:
        return "agent"
    # Max iterations reached
    state["final_report"] = state.get("draft_answer", "Rapor oluşturulamadı.")
    return "end"


# =============================================================================
# BUILD GRAPH
# =============================================================================
def build_react_agent():
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("reflect", reflection_node)
    
    # Entry
    workflow.set_entry_point("agent")
    
    # Edges
    workflow.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "reflect": "reflect",
        "end": END
    })
    workflow.add_edge("tools", "agent")
    workflow.add_conditional_edges("reflect", after_reflection, {
        "agent": "agent",
        "end": END
    })
    
    return workflow.compile()


react_agent = build_react_agent()


def run_react_agent(user_query: str) -> str:
    print("="*50)
    print("  FINANCIAL RESEARCH AGENT v5 (with Query Rewriter)")
    print("="*50)
    print(f"Original Query: {user_query}")
    
    # Pre-LLM: Sorguyu yeniden yaz
    rewritten_query = rewrite_query(user_query)
    
    print("="*50)
    
    result = react_agent.invoke({
        "messages": [HumanMessage(content=rewritten_query)],
        "user_query": user_query,  # Orijinal sorguyu sakla (reflection için)
        "tool_results": {},
        "iteration": 0,
        "draft_answer": "",
        "final_report": "",
        "needs_more_work": False
    })
    
    print("\n" + "="*50)
    print("  FINAL REPORT")
    print("="*50)
    
    report = result.get("final_report", "")
    print(report)
    return report


if __name__ == "__main__":
    run_react_agent("Gümüş alınır mı?")
