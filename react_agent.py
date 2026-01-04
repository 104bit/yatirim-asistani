"""
ReAct Agent v5 - With bind_tools
=================================
Native LangGraph tool calling with Reflection.
"""

import os
import time
from typing import TypedDict, Annotated
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from tools.market_tools import ALL_TOOLS

# Rate limit delay
RATE_LIMIT_DELAY = 2


# =============================================================================
# STATE
# =============================================================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    iteration: int
    draft_answer: str
    final_report: str
    needs_more_work: bool


# =============================================================================
# SYSTEM PROMPT (Updated - no <tool> format needed)
# =============================================================================
REACT_SYSTEM_PROMPT = f"""Sen Türkiye'nin en iyi Finansal Araştırma Ajansısın.
Bugünün tarihi: {datetime.now().strftime('%d %B %Y')}

## TEMEL PRENSİPLER
1. **SOMUT VERİ** → Her raporda fiyat, değişim, RSI gibi sayılar olmalı
2. **ARAŞTIR, UYDURMA** → Veri bulamazsan açıkça söyle, asla tahmin etme
3. **PROAKTİF OL** → Belirsiz sorularda bile araştır, pasif kalma
4. **NİYETİ ANLA** → Kullanıcının gerçek amacını çöz, en uygun tool'u seç

## ÖNEMLİ: ÇALIŞMA PRENSİBİ
Hazırladığın cevap kullanıcıya GİTMEYECEK. Önce katı bir "REFLECTION AGENT" (Denetçi) tarafından kontrol edilecek.
Denetçi sana eksiklerini söyleyip tekrar iş yaptıracak.
BU YÜZDEN:
- Kullanıcıya ASLA soru sorma (Denetçi cevap veremez).
- Eksik bilgi olsa bile elindeki verilerle EN İYİ TASLAK RAPORU hazırla.
- "Spesifik konu belirtin" demek yerine, genel bir analiz yap.

## ARAÇLARIN
| Araç | Ne Zaman Kullan |
|------|-----------------|
| analyze_stock(symbol) | Spesifik varlık analizi (altın, bitcoin, THYAO vb.) |
| get_news(company) | Haberler, piyasa yorumları ve sentiment analizi için (ÖNCELİKLİ) |
| scan_sector(sector) | Sektör karşılaştırması (banka, holding, enerji) |
| web_search(query) | Sadece veri bulunamazsa kullan |
| compare(symbols) | 2-3 varlık karşılaştırması |
| get_forex(pair) | Döviz kurları (USDTRY, EURTRY) |

## ÖRNEK KARARLAR (Bunlardan öğren!)

### Spesifik Varlık Sorusu
Soru: "Bakır alınır mı?"
→ analyze_stock + get_news kullan

### Belirsiz/Genel Soru  
Soru: "Ne alayım?" veya "Zengin olmak istiyorum"
→ web_search + scan_sector + analyze_stock kullan
→ Sonra çeşitlendirilmiş portföy öner

### Geçmiş Tarihli Soru
Soru: "2024'te hangi hisseler kazandırdı?"
→ web_search kullan

### Gelecek Tahmini
Soru: "2030'da Bitcoin ne olur?"
→ analyze_stock + get_news kullan
→ Mevcut veriyi ver + "Gelecek tahminleri kesin değildir" disclaimer ekle

### Sektör Sorusu
Soru: "Banka sektörü nasıl?"
→ scan_sector kullan

### Fantezi/İmkansız Soru
Soru: "Mars'taki altın madeni hissesi?"
→ Tool kullanma! Cevap: "Bu gerçek bir finansal varlık değil."

### Anlamsız Sorgu
Soru: "asdfghjkl" veya sadece "yatırım"
→ Tool kullanma! Cevap: "Lütfen spesifik bir varlık veya soru belirtin."

## RAPOR FORMATI
Her raporda şunlar olmalı:
- Fiyat ve teknik veriler
- Güncel haberler ve sentiment
- Net tavsiye (AL/SAT/TUT) + gerekçe
"""

REFLECTION_PROMPT = """Sen KIDEMLİ BİR FİNANS EDİTÖRÜSÜN.
Görevin: Hazırlanan yatırım raporunu kontrol etmek ve yayına uygun olup olmadığına karar vermek.
Amacın mükemmel değil, "yeterli ve doğru" bilgi sunmak.

KULLANICI SORUSU: {query}

TASLAK Rapor:
{answer}

## KONTROL LİSTESİ (Checklist)

1. **Fiyat Bilgisi:** Raporda herhangi bir fiyat veya değer geçiyor mu?
2. **Yönlendirme:** Okuyucuya bir fikir (pozitif/negatif) veriyor mu?
3. **Akış:** Rapor anlaşılır mı?

---

## KARAR

Eğer rapor genel olarak makul ve kullanıcıya faydalıysa:
"TAMAM" yaz.
Eğer KRİTİK bir eksik varsa (örneğin hiç fiyat yoksa):
"DEVAM: [eksik veriyi alacak tool]" formatında komut ver.

Gereksiz detaylara takılma.
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
- Geçmiş veri → web_search
- Spesifik varlık → analyze_stock + get_news
- Genel soru → web_search + scan_sector + analyze_stock
- Sektör → scan_sector
- Karşılaştırma → compare

## ÇIKTI FORMATI:
Soruyu şu şekilde yeniden yaz:
"[Orijinal niyet]. [Kullanılacak tool'lar: tool1, tool2]"

Sadece yeniden yazılmış sorguyu döndür, başka açıklama yapma.
"""


def rewrite_query(user_query: str) -> str:
    """Pre-LLM: Kullanıcı sorgusunu analiz et ve agent için optimize et."""
    print(f"\n[Query Rewriter] Analyzing: {user_query}")
    
    try:
        llm = get_llm()
        prompt = QUERY_REWRITER_PROMPT.format(query=user_query)
        response = llm.invoke([HumanMessage(content=prompt)])
        rewritten = response.content.strip()
        
        print(f"[Query Rewriter] Rewritten: {rewritten}")
        return rewritten
    except Exception as e:
        print(f"[Query Rewriter] Error: {e}, using original query")
        return user_query


# =============================================================================
# LLM SETUP
# =============================================================================
def get_llm():
    """Get base LLM instance."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if openrouter_key:
        return ChatOpenAI(
            model="xiaomi/mimo-v2-flash:free",
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
        raise ValueError("No API key found. Set OPENROUTER_API_KEY or GOOGLE_API_KEY.")


def get_llm_with_tools():
    """Get LLM with tools bound for native tool calling."""
    return get_llm().bind_tools(ALL_TOOLS)


# =============================================================================
# TOOL NODE (using LangGraph prebuilt)
# =============================================================================
tool_node = ToolNode(ALL_TOOLS)


# =============================================================================
# AGENT NODE
# =============================================================================
def agent_node(state: AgentState) -> AgentState:
    """Agent node that uses native tool calling."""
    print("\n[Agent] Thinking...")
    time.sleep(RATE_LIMIT_DELAY)
    
    messages = state["messages"]
    
    # Ensure system prompt is present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=REACT_SYSTEM_PROMPT)] + list(messages)
    
    # Check if reflection said to continue
    if state.get("needs_more_work"):
        messages = list(messages) + [HumanMessage(content="Cevabın yetersiz bulundu. Daha fazla veri topla ve analiz yap.")]
    
    # Call LLM with bound tools
    llm = get_llm_with_tools()
    response = llm.invoke(messages)
    
    # Update iteration count
    new_iteration = state.get("iteration", 0) + 1
    
    # Check if there are tool calls
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"[Agent] Found {len(response.tool_calls)} tool calls:")
        for tc in response.tool_calls:
            print(f"  → {tc['name']}({tc['args']})")
    else:
        print("[Agent] No tool calls, generating response...")
        # Extract content as draft answer
        content = response.content if hasattr(response, 'content') else str(response)
        state["draft_answer"] = content
    
    return {
        "messages": [response],
        "iteration": new_iteration,
        "needs_more_work": False,
        "draft_answer": state.get("draft_answer", ""),
        "final_report": state.get("final_report", ""),
        "user_query": state.get("user_query", "")
    }


# =============================================================================
# REFLECTION NODE
# =============================================================================
def reflection_node(state: AgentState) -> AgentState:
    """Evaluate answer quality and decide if more work is needed."""
    print("\n[Reflection] Evaluating answer quality...")
    time.sleep(RATE_LIMIT_DELAY)
    
    llm = get_llm()
    
    prompt = REFLECTION_PROMPT.format(
        query=state["user_query"],
        answer=state["draft_answer"]
    )
    
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    
    print(f"[Reflection] Result: {result[:50]}...")
    
    if "TAMAM" in result.upper():
        print("[Reflection] Answer approved!")
        return {
            "messages": state["messages"],
            "final_report": state["draft_answer"],
            "needs_more_work": False,
            "draft_answer": state["draft_answer"],
            "iteration": state["iteration"],
            "user_query": state["user_query"]
        }
    else:
        print("[Reflection] Needs more work...")
        return {
            "messages": state["messages"],
            "needs_more_work": True,
            "draft_answer": state["draft_answer"],
            "final_report": "",
            "iteration": state["iteration"],
            "user_query": state["user_query"]
        }


# =============================================================================
# ROUTING
# =============================================================================
def should_continue(state: AgentState) -> str:
    """Route based on agent response."""
    # If we have a final report, we're done
    if state.get("final_report"):
        return "end"
    
    # If we have a draft answer, go to reflection
    if state.get("draft_answer"):
        return "reflect"
    
    # Check last message for tool calls
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        if hasattr(last, 'tool_calls') and last.tool_calls:
            if state.get("iteration", 0) < 3:
                return "tools"
    
    # No tool calls and no draft - check content
    if messages:
        last = messages[-1]
        content = last.content if hasattr(last, 'content') else ""
        if content:
            # Treat as draft answer
            state["draft_answer"] = content
            return "reflect"
    
    return "end"


def after_reflection(state: AgentState) -> str:
    """Route after reflection."""
    if state.get("final_report"):
        return "end"
    if state.get("needs_more_work") and state.get("iteration", 0) < 3:
        return "agent"
    # Max iterations reached - use whatever we have
    if not state.get("final_report"):
        state["final_report"] = state.get("draft_answer", "Rapor oluşturulamadı.")
    return "end"


# =============================================================================
# BUILD GRAPH
# =============================================================================
def build_react_agent():
    """Build the ReAct agent graph with native tool calling."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("reflect", reflection_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edges
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


# Build the agent
react_agent = build_react_agent()


def run_react_agent(user_query: str) -> str:
    """Run the ReAct agent with a user query."""
    print("="*50)
    print("  FINANCIAL RESEARCH AGENT v6 (bind_tools)")
    print("="*50)
    print(f"Original Query: {user_query}")
    
    # Pre-LLM: Rewrite query (DISABLED for optimization)
    # rewritten_query = rewrite_query(user_query)
    rewritten_query = user_query
    
    print("="*50)
    
    result = react_agent.invoke({
        "messages": [HumanMessage(content=rewritten_query)],
        "user_query": user_query,
        "iteration": 0,
        "draft_answer": "",
        "final_report": "",
        "needs_more_work": False
    })
    
    print("\n" + "="*50)
    print("  FINAL REPORT")
    print("="*50)
    
    report = result.get("final_report", "")
    
    # Fallback if no final report
    if not report:
        report = result.get("draft_answer", "")
        if not report:
            # Last resort: use last message content
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    report = last_msg.content
    
    if not report:
        report = "Rapor oluşturulamadı. (Iterasyon limiti veya teknik hata)"
        
    print(report)
    return report


if __name__ == "__main__":
    run_react_agent("Gümüş alınır mı?")
