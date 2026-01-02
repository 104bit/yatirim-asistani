"""
Financial Research Agent
=========================
User-facing entry point for the ReAct agent.

Usage:
    py research.py "Sabancı Holding hakkında analiz yap"
    py research.py --interactive
"""

import argparse
import sys

from react_agent import run_react_agent


def save_report(report, filename):
    """Save report to file, handling different response formats."""
    with open(filename, 'w', encoding='utf-8') as f:
        if isinstance(report, list):
            # Handle list response (from Gemini)
            report_text = "\n".join([
                item.get("text", str(item)) if isinstance(item, dict) else str(item) 
                for item in report
            ])
        else:
            report_text = str(report)
        f.write(report_text)
    print(f"\n[Rapor kaydedildi: {filename}]")


def main():
    parser = argparse.ArgumentParser(description="Financial Research Agent with LLM Tool Use")
    parser.add_argument("query", nargs="?", help="Your financial research question")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("="*60)
        print("   FİNANSAL ARAŞTIRMA AJANI")
        print("   (Çıkmak için 'exit' yazın)")
        print("="*60)
        
        while True:
            try:
                query = input("\n📊 Sorunuz: ").strip()
                
                if query.lower() in ["exit", "quit", "q", "çıkış"]:
                    print("Görüşürüz! 👋")
                    break
                
                if not query:
                    continue
                
                report = run_react_agent(query)
                filename = f"report_{query[:20].replace(' ', '_')}.md"
                save_report(report, filename)
                
            except KeyboardInterrupt:
                print("\nÇıkış...")
                break
    
    elif args.query:
        report = run_react_agent(args.query)
        save_report(report, "financial_report.md")
    
    else:
        # Default query
        default_query = "Sabancı Holding (SAHOL.IS) hakkında kapsamlı yatırım analizi yap"
        print(f"Default query: {default_query}")
        report = run_react_agent(default_query)
        save_report(report, "financial_report.md")


if __name__ == "__main__":
    main()
